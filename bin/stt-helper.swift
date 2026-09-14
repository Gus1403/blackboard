// stt-helper: one utterance of streaming on-device speech recognition.
// Prints NDJSON to stdout:
//   {"type":"level","v":0.42}       ~10Hz mic RMS for the orb
//   {"type":"partial","text":"..."}  live transcript while speaking
//   {"type":"final","text":"..."}    then exits 0
// Endpointing: transcript stable for STABLE_MS after speech began, or
// NO_SPEECH_MS with no transcript at all (final ""), or 60s hard cap.
// With --ptt the parent owns the endpoint: neither stability nor no-speech
// applies, only the hard cap and the stdin stop signal (a line, or EOF).
// With --stdin-audio it does not touch the mic at all: the parent streams mono
// float32 PCM at 16kHz on stdin and EOF ends the utterance (see the audio
// section for why).
// Usage: stt-helper [locale] [--locale id] [--ptt] [--stdin-audio] [--version]

import AVFoundation
import Foundation
import Speech

let VERSION = 3
let STDIN_SR = 16000.0
let STABLE_MS = 800.0
let NO_SPEECH_MS = 8000.0
let HARD_CAP_MS = 60000.0

func emit(_ obj: [String: Any]) {
    if let d = try? JSONSerialization.data(withJSONObject: obj),
       let s = String(data: d, encoding: .utf8) {
        print(s)
        fflush(stdout)
    }
}

func note(_ msg: String) {
    FileHandle.standardError.write(("[stt-helper] " + msg + "\n").data(using: .utf8)!)
}

func fail(_ msg: String) -> Never {
    emit(["type": "error", "message": msg])
    exit(2)
}

// --- arguments ---------------------------------------------------------------
// A bare positional locale stays supported. --version answers before any mic or
// permission work, so the caller can spot a stale binary cheaply.
var localeID = "pt-BR"
var ptt = false
var stdinAudio = false
var argv = CommandLine.arguments.dropFirst().makeIterator()
while let arg = argv.next() {
    switch arg {
    case "--version":
        print("stt-helper \(VERSION)")
        exit(0)
    case "--ptt":
        ptt = true
    case "--stdin-audio":
        stdinAudio = true
    case "--locale":
        guard let v = argv.next() else { fail("--locale needs a value") }
        localeID = v
    default:
        if arg.hasPrefix("-") { fail("unknown argument \(arg)") }
        localeID = arg
    }
}

// --- authorization -----------------------------------------------------------
let authSem = DispatchSemaphore(value: 0)
var authStatus = SFSpeechRecognizerAuthorizationStatus.notDetermined
SFSpeechRecognizer.requestAuthorization { s in authStatus = s; authSem.signal() }
_ = authSem.wait(timeout: .now() + 30)
guard authStatus == .authorized else {
    fail("speech recognition not authorized (status=\(authStatus.rawValue)) — grant in System Settings > Privacy > Speech Recognition")
}

guard let recognizer = SFSpeechRecognizer(locale: Locale(identifier: localeID)) else {
    fail("no recognizer for locale \(localeID)")
}

let request = SFSpeechAudioBufferRecognitionRequest()
request.shouldReportPartialResults = true
if recognizer.supportsOnDeviceRecognition {
    request.requiresOnDeviceRecognition = true
}
note("locale=\(localeID) available=\(recognizer.isAvailable) "
     + "onDevice=\(recognizer.supportsOnDeviceRecognition) stdinAudio=\(stdinAudio)")
if #available(macOS 13, *) { request.addsPunctuation = true }

// --- shared state ------------------------------------------------------------
final class State {
    var lastPartial = ""
    var lastChange = Date()
    var sawSpeech = false
    var done = false
    let lock = NSLock()
}
let state = State()
let started = Date()

func finish(_ text: String) {
    state.lock.lock()
    if state.done { state.lock.unlock(); return }
    state.done = true
    state.lock.unlock()
    emit(["type": "final", "text": text])
    exit(0)
}

// --- recognition task --------------------------------------------------------
let task = recognizer.recognitionTask(with: request) { result, error in
    if let result = result {
        let text = result.bestTranscription.formattedString
        state.lock.lock()
        if text != state.lastPartial {
            state.lastPartial = text
            state.lastChange = Date()
            if !text.isEmpty { state.sawSpeech = true }
        }
        state.lock.unlock()
        if !text.isEmpty { emit(["type": "partial", "text": text]) }
        if result.isFinal { finish(text) }
    }
    if let error {
        note("recognizer error: \(error.localizedDescription)")
        state.lock.lock()
        let text = state.lastPartial
        state.lock.unlock()
        finish(text)  // recognizer errors after endAudio still carry the transcript
    }
}
_ = task

// --- shutdown ----------------------------------------------------------------
// Shared by the watchdog and the stdin stop signal; both may fire, and both may
// beat the recognizer's own isFinal — finish() is idempotent, so that is fine.
func stopListening(_ partial: String) {
    engine.stop()
    request.endAudio()
    // If the recognizer never delivers isFinal, exit with what we have.
    DispatchQueue.global().asyncAfter(deadline: .now() + 1.5) { finish(partial) }
}

// --- audio -------------------------------------------------------------------
// Two sources. --stdin-audio takes raw PCM from the parent, which is the mode
// voiced uses: microphone access is granted to the python daemon, and this
// helper — a separate signed binary with its own identity — does not inherit
// it, so owning the mic here yields a stream that never delivers a single
// buffer. Speech Recognition authorisation, checked above, does carry over.
let engine = AVAudioEngine()

func startMic() {
    let input = engine.inputNode
    let fmt = input.outputFormat(forBus: 0)
    var levelCounter = 0
    input.installTap(onBus: 0, bufferSize: 1600, format: fmt) { buffer, _ in
        request.append(buffer)
        levelCounter += 1
        if levelCounter % 3 == 0, let ch = buffer.floatChannelData {
            let n = Int(buffer.frameLength)
            var sum: Float = 0
            for i in 0..<n { sum += ch[0][i] * ch[0][i] }
            let rms = sqrt(sum / Float(max(n, 1)))
            emit(["type": "level", "v": min(1.0, Double(rms) * 12)])
        }
    }
    engine.prepare()
    do { try engine.start() } catch { fail("mic start failed: \(error.localizedDescription)") }
}

/// Reads mono float32 PCM at STDIN_SR from stdin until EOF, then endpoints.
/// The parent publishes its own levels, so this path emits none.
func startStdinAudio() {
    guard let fmt = AVAudioFormat(commonFormat: .pcmFormatFloat32,
                                  sampleRate: STDIN_SR, channels: 1,
                                  interleaved: false) else {
        fail("could not build input format")
    }
    DispatchQueue.global().async {
        let handle = FileHandle.standardInput
        let frames = 1600  // 100ms
        var appended = 0
        while true {
            let data = handle.availableData
            if data.isEmpty { break }  // EOF: the parent released the key
            data.withUnsafeBytes { raw in
                let floats = raw.bindMemory(to: Float.self)
                var offset = 0
                while offset < floats.count {
                    let n = min(frames, floats.count - offset)
                    guard let buf = AVAudioPCMBuffer(pcmFormat: fmt,
                                                     frameCapacity: AVAudioFrameCount(n))
                    else { break }
                    buf.frameLength = AVAudioFrameCount(n)
                    if let dst = buf.floatChannelData?[0] {
                        for i in 0..<n { dst[i] = floats[offset + i] }
                    }
                    request.append(buf)
                    appended += 1
                    offset += n
                }
            }
        }
        note("stdin EOF after \(appended) buffers")
        state.lock.lock()
        let partial = state.lastPartial
        state.lock.unlock()
        stopListening(partial)
    }
}

if stdinAudio { startStdinAudio() } else { startMic() }

// --- endpoint watchdog -------------------------------------------------------
let timer = DispatchSource.makeTimerSource()
timer.schedule(deadline: .now() + 0.2, repeating: 0.2)
timer.setEventHandler {
    state.lock.lock()
    let saw = state.sawSpeech
    let sinceChange = Date().timeIntervalSince(state.lastChange) * 1000
    let sinceStart = Date().timeIntervalSince(started) * 1000
    let partial = state.lastPartial
    state.lock.unlock()
    if (!ptt && saw && sinceChange > STABLE_MS)
        || (!ptt && !saw && sinceStart > NO_SPEECH_MS)
        || sinceStart > HARD_CAP_MS {
        stopListening(partial)
    }
}
timer.resume()

// --- stdin stop signal -------------------------------------------------------
// Only armed in --ptt: a daemon-launched helper inherits /dev/null on stdin,
// whose instant EOF would endpoint the utterance before it began.
if ptt && !stdinAudio {
    DispatchQueue.global().async {
        _ = readLine()  // nil at EOF, a String if the parent writes anything
        state.lock.lock()
        let partial = state.lastPartial
        state.lock.unlock()
        stopListening(partial)
    }
}

RunLoop.main.run()

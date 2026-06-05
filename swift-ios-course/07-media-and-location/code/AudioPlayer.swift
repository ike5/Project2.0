import Foundation
import AVFoundation

// Minimal AVFoundation audio playback. Note the DELEGATE callback for "finished playing"
// — another Objective-C-heritage pattern.
final class AudioPlayer: NSObject, ObservableObject, AVAudioPlayerDelegate {
    private var player: AVAudioPlayer?
    @Published var isPlaying = false

    func play(url: URL) {
        do {
            player = try AVAudioPlayer(contentsOf: url)
            player?.delegate = self
            player?.prepareToPlay()
            player?.play()
            isPlaying = true
        } catch {
            print("audio error:", error.localizedDescription)
            isPlaying = false
        }
    }

    func stop() {
        player?.stop()
        isPlaying = false
    }

    // MARK: AVAudioPlayerDelegate
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        isPlaying = false
    }
}

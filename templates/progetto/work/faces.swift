import Vision
import AppKit
let dir = CommandLine.arguments[1]
let files = try! FileManager.default.contentsOfDirectory(atPath: dir).filter { $0.hasSuffix(".jpg") }.sorted()
var out: [String] = []
for f in files {
  let url = URL(fileURLWithPath: dir + "/" + f)
  let req = VNDetectFaceRectanglesRequest()
  let h = VNImageRequestHandler(url: url)
  try? h.perform([req])
  if let r = (req.results ?? []).max(by: { $0.boundingBox.width < $1.boundingBox.width }) {
    let b = r.boundingBox
    out.append("\(f) \(b.midX) \(1 - b.midY) \(b.width) \(b.height)")
  } else { out.append("\(f) nan nan nan nan") }
}
try! out.joined(separator: "\n").write(toFile: dir + "/faces.txt", atomically: true, encoding: .utf8)

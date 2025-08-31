import SwiftUI
import AppKit

// MARK: - About View

struct AboutView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 60))
                .foregroundColor(.accentColor)
            
            VStack(spacing: 8) {
                Text("CLAUDE")
                    .font(.title)
                    .fontWeight(.bold)
                
                Text("Code-Library-Aware Unified Development Environment")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            
            VStack(spacing: 4) {
                Text("Version 0.1.0")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text("© 2024 CLAUDE Development Team")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .padding()
    }
}

// MARK: - Directory Picker

struct DirectoryPickerView: View {
    @Binding var selectedDirectory: String
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Select Directory")
                .font(.title2)
                .fontWeight(.semibold)
            
            DirectoryPicker(selectedDirectory: $selectedDirectory)
            
            HStack {
                Button("Cancel") {
                    dismiss()
                }
                
                Spacer()
                
                Button("Select") {
                    dismiss()
                }
                .buttonStyle(.borderedProminent)
                .disabled(selectedDirectory.isEmpty)
            }
            .padding()
        }
        .frame(width: 600, height: 400)
        .padding()
    }
}

// MARK: - Directory Picker Component

struct DirectoryPicker: NSViewRepresentable {
    @Binding var selectedDirectory: String
    
    func makeNSView(context: Context) -> NSView {
        let button = NSButton(title: "Select Directory", target: context.coordinator, action: #selector(Coordinator.selectDirectory))
        button.target = context.coordinator
        return button
    }
    
    func updateNSView(_ nsView: NSView, context: Context) {
        if let button = nsView as? NSButton {
            button.title = selectedDirectory.isEmpty ? "Select Directory" : selectedDirectory
        }
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject {
        var parent: DirectoryPicker
        
        init(_ parent: DirectoryPicker) {
            self.parent = parent
        }
        
        @objc func selectDirectory() {
            let panel = NSOpenPanel()
            panel.allowsMultipleSelection = false
            panel.canChooseDirectories = true
            panel.canChooseFiles = false
            panel.allowsOtherFileTypes = false
            
            if panel.runModal() == .OK {
                if let url = panel.urls.first {
                    parent.selectedDirectory = url.path
                }
            }
        }
    }
}
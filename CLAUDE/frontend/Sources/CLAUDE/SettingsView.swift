import SwiftUI

// MARK: - Settings View

struct SettingsView: View {
    @State private var selectedTab = SettingsTab.general
    @State private var apiHost: String = "localhost"
    @State private var apiPort: String = "8000"
    @State private var autoStartMonitoring: Bool = true
    @State private var maxContextChunks: Double = 5
    @State private var similarityThreshold: Double = 0.3
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Settings")
                    .font(.title)
                    .fontWeight(.bold)
                
                Spacer()
                
                Button("Done") {
                    // Dismiss settings
                }
                .buttonStyle(.borderedProminent)
            }
            .padding()
            
            // Tab View
            TabView(selection: $selectedTab) {
                GeneralSettingsView(
                    apiHost: $apiHost,
                    apiPort: $apiPort,
                    autoStartMonitoring: $autoStartMonitoring
                )
                .tag(SettingsTab.general)
                .tabItem {
                    Label("General", systemImage: "gear")
                }
                
                AdvancedSettingsView(
                    maxContextChunks: $maxContextChunks,
                    similarityThreshold: $similarityThreshold
                )
                .tag(SettingsTab.advanced)
                .tabItem {
                    Label("Advanced", systemImage: "slider.horizontal.3")
                }
            }
        }
        .frame(width: 500, height: 400)
    }
}

// MARK: - Settings Tab Enum

enum SettingsTab {
    case general
    case advanced
}

// MARK: - General Settings View

struct GeneralSettingsView: View {
    @Binding var apiHost: String
    @Binding var apiPort: String
    @Binding var autoStartMonitoring: Bool
    
    var body: some View {
        Form {
            Section("API Configuration") {
                TextField("Host", text: $apiHost)
                TextField("Port", text: $apiPort)
            }
            
            Section("Monitoring") {
                Toggle("Auto-start Monitoring", isOn: $autoStartMonitoring)
            }
        }
        .padding()
    }
}

// MARK: - Advanced Settings View

struct AdvancedSettingsView: View {
    @Binding var maxContextChunks: Double
    @Binding var similarityThreshold: Double
    
    var body: some View {
        Form {
            Section("RAG Configuration") {
                Slider(value: $maxContextChunks, in: 1...20) {
                    Text("Max Context Chunks")
                }
                Text("\(Int(maxContextChunks))")
                    .foregroundColor(.secondary)
                
                Slider(value: $similarityThreshold, in: 0...1) {
                    Text("Similarity Threshold")
                }
                Text(String(format: "%.2f", similarityThreshold))
                    .foregroundColor(.secondary)
            }
        }
        .padding()
    }
}
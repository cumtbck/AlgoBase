import SwiftUI

struct ContentView: View {
    @State private var query: String = ""
    @State private var response: String = ""
    @State private var isLoading: Bool = false
    @State private var selectedDirectory: String = ""
    @State private var systemStatus: SystemStatus = .unknown
    @State private var showingDirectoryPicker = false
    @State private var showingSettings = false
    @State private var retrievedContext: [CodeContext] = []
    @State private var selectedLanguage: String = "Python"
    @State private var contextType: ContextType = .implementation
    
    private let apiService = APIService()
    private let languages = ["Python", "JavaScript", "TypeScript", "Java", "C++", "Swift", "Go", "Rust"]
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HeaderView(
                systemStatus: systemStatus,
                onSettingsTap: { showingSettings = true }
            )
            
            // Main Content
            HSplitView {
                // Left Panel - Input and Context
                VStack(spacing: 16) {
                    // Directory Selection
                    DirectorySelectorView(
                        selectedDirectory: selectedDirectory,
                        onDirectorySelect: { showingDirectoryPicker = true }
                    )
                    
                    // Query Input
                    QueryInputView(
                        query: $query,
                        selectedLanguage: $selectedLanguage,
                        contextType: $contextType,
                        languages: languages,
                        onSubmit: handleSubmit
                    )
                    
                    // Context Display
                    ContextDisplayView(context: retrievedContext)
                    
                    Spacer()
                }
                .padding()
                .frame(minWidth: 300)
                
                // Right Panel - Response
                ResponseView(
                    response: response,
                    isLoading: isLoading,
                    onCopyCode: handleCopyCode
                )
            }
            
            // Status Bar
            StatusBarView(status: systemStatus)
        }
        .sheet(isPresented: $showingDirectoryPicker) {
            DirectoryPickerView(selectedDirectory: $selectedDirectory)
        }
        .sheet(isPresented: $showingSettings) {
            SettingsView()
        }
        .onAppear(perform: checkSystemStatus)
        .task {
            await monitorSystemStatus()
        }
    }
    
    private func handleSubmit() {
        guard !query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        Task {
            await generateResponse()
        }
    }
    
    private func generateResponse() async {
        isLoading = true
        response = ""
        retrievedContext = []
        
        do {
            let request = QueryRequest(
                question: query,
                language: selectedLanguage.lowercased(),
                contextType: contextType.rawValue,
                maxContextChunks: 5,
                similarityThreshold: 0.3
            )
            
            let result: QueryResponse = try await apiService.post("/query", body: request)
            
            await MainActor.run {
                response = result.answer
                retrievedContext = result.retrievedContext.map { context in
                    CodeContext(
                        content: context.content,
                        filePath: context.filePath,
                        lineStart: context.lineStart,
                        lineEnd: context.lineEnd,
                        score: context.score,
                        language: context.language,
                        chunkType: context.chunkType
                    )
                }
                isLoading = false
            }
        } catch {
            await MainActor.run {
                response = "Error: \(error.localizedDescription)"
                isLoading = false
            }
        }
    }
    
    private func handleCopyCode() {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(response, forType: .string)
    }
    
    private func checkSystemStatus() {
        Task {
            do {
                let status: SystemStatusResponse = try await apiService.get("/system/status")
                await MainActor.run {
                    systemStatus = status.status == "healthy" ? .healthy : .degraded
                }
            } catch {
                await MainActor.run {
                    systemStatus = .offline
                }
            }
        }
    }
    
    private func monitorSystemStatus() async {
        while true {
            try? await Task.sleep(nanoseconds: 30_000_000_000) // 30 seconds
            checkSystemStatus()
        }
    }
}

// MARK: - Supporting Views

struct HeaderView: View {
    let systemStatus: SystemStatus
    let onSettingsTap: () -> Void
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("CLAUDE")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Code-Library-Aware Unified Development Environment")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            HStack(spacing: 12) {
                StatusIndicator(status: systemStatus)
                
                Button(action: onSettingsTap) {
                    Image(systemName: "gearshape.fill")
                        .font(.title2)
                }
                .buttonStyle(PlainButtonStyle())
                .help("Settings")
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
    }
}

struct DirectorySelectorView: View {
    let selectedDirectory: String
    let onDirectorySelect: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Codebase Directory")
                .font(.headline)
            
            HStack {
                Text(selectedDirectory.isEmpty ? "No directory selected" : selectedDirectory)
                    .foregroundColor(selectedDirectory.isEmpty ? .secondary : .primary)
                    .truncationMode(.middle)
                
                Spacer()
                
                Button("Select Directory") {
                    onDirectorySelect()
                }
                .buttonStyle(.bordered)
            }
            .padding(8)
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(8)
        }
    }
}

struct QueryInputView: View {
    @Binding var query: String
    @Binding var selectedLanguage: String
    @Binding var contextType: ContextType
    let languages: [String]
    let onSubmit: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Query")
                .font(.headline)
            
            // Language and Context Type Selection
            HStack {
                Picker("Language", selection: $selectedLanguage) {
                    ForEach(languages, id: \.self) { language in
                        Text(language).tag(language)
                    }
                }
                .pickerStyle(.menu)
                
                Picker("Context", selection: $contextType) {
                    ForEach(ContextType.allCases, id: \.self) { type in
                        Text(type.displayName).tag(type)
                    }
                }
                .pickerStyle(.menu)
            }
            
            // Query Input
            ZStack(alignment: .topLeading) {
                if query.isEmpty {
                    Text("Enter your coding question or request...")
                        .foregroundColor(.secondary)
                        .padding(.leading, 5)
                        .padding(.top, 8)
                }
                
                TextEditor(text: $query)
                    .font(.body)
                    .scrollContentBackground(.hidden)
                    .background(Color(NSColor.textBackgroundColor))
                    .cornerRadius(8)
            }
            .frame(height: 100)
            
            // Submit Button
            Button("Generate") {
                onSubmit()
            }
            .buttonStyle(.borderedProminent)
            .disabled(query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
        }
    }
}

struct ContextDisplayView: View {
    let context: [CodeContext]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Retrieved Context")
                .font(.headline)
            
            if context.isEmpty {
                Text("No context retrieved yet")
                    .foregroundColor(.secondary)
                    .italic()
            } else {
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 8) {
                        ForEach(context, id: \.filePath) { ctx in
                            ContextCard(context: ctx)
                        }
                    }
                }
                .frame(maxHeight: 200)
            }
        }
    }
}

struct ContextCard: View {
    let context: CodeContext
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(context.filePath)
                    .font(.caption)
                    .fontWeight(.medium)
                
                Spacer()
                
                Text(String(format: "%.2f", context.score))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Text("Lines \(context.lineStart)-\(context.lineEnd) • \(context.language) • \(context.chunkType)")
                .font(.caption2)
                .foregroundColor(.secondary)
            
            Text(context.content)
                .font(.system(.body, design: .monospaced))
                .padding(8)
                .background(Color(NSColor.textBackgroundColor))
                .cornerRadius(4)
        }
        .padding(8)
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }
}

struct ResponseView: View {
    let response: String
    let isLoading: Bool
    let onCopyCode: () -> Void
    
    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Text("Response")
                    .font(.headline)
                
                Spacer()
                
                if !response.isEmpty {
                    Button("Copy Code") {
                        onCopyCode()
                    }
                    .buttonStyle(.bordered)
                }
            }
            
            if isLoading {
                VStack(spacing: 12) {
                    ProgressView()
                        .scaleEffect(1.2)
                    Text("Generating response...")
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if response.isEmpty {
                Text("Enter a query to generate a response")
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    Text(response)
                        .font(.system(.body, design: .monospaced))
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .background(Color(NSColor.textBackgroundColor))
                .cornerRadius(8)
            }
        }
        .padding()
    }
}

struct StatusBarView: View {
    let status: SystemStatus
    
    var body: some View {
        HStack {
            StatusIndicator(status: status)
            
            Text(status.displayName)
                .font(.caption)
                .foregroundColor(.secondary)
            
            Spacer()
            
            Text("v0.1.0")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal)
        .padding(.vertical, 4)
        .background(Color(NSColor.controlBackgroundColor))
    }
}

struct StatusIndicator: View {
    let status: SystemStatus
    
    var body: some View {
        Circle()
            .fill(status.color)
            .frame(width: 8, height: 8)
    }
}

// MARK: - Supporting Types

enum SystemStatus: String, CaseIterable {
    case healthy = "healthy"
    case degraded = "degraded"
    case offline = "offline"
    case unknown = "unknown"
    
    var displayName: String {
        switch self {
        case .healthy: return "Healthy"
        case .degraded: return "Degraded"
        case .offline: return "Offline"
        case .unknown: return "Unknown"
        }
    }
    
    var color: Color {
        switch self {
        case .healthy: return .green
        case .degraded: return .yellow
        case .offline: return .red
        case .unknown: return .gray
        }
    }
}

enum ContextType: String, CaseIterable {
    case implementation = "implementation"
    case explanation = "explanation"
    case debug = "debug"
    
    var displayName: String {
        switch self {
        case .implementation: return "Implementation"
        case .explanation: return "Explanation"
        case .debug: return "Debug"
        }
    }
}

struct CodeContext: Identifiable {
    let id = UUID()
    let content: String
    let filePath: String
    let lineStart: Int
    let lineEnd: Int
    let score: Double
    let language: String
    let chunkType: String
}

// MARK: - Preview

#Preview {
    ContentView()
}
import Foundation

// MARK: - API Service

class APIService {
    private let baseURL = "http://localhost:8000"
    private let session = URLSession.shared
    
    func get<T: Decodable>(_ endpoint: String) async throws -> T {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.httpError(httpResponse.statusCode)
        }
        
        do {
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }
    
    func post<T: Decodable, U: Encodable>(_ endpoint: String, body: U) async throws -> T {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            request.httpBody = try JSONEncoder().encode(body)
        } catch {
            throw APIError.encodingError(error)
        }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.httpError(httpResponse.statusCode)
        }
        
        do {
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }
}

enum APIError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(Int)
    case decodingError(Error)
    case encodingError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response"
        case .httpError(let statusCode):
            return "HTTP error: \(statusCode)"
        case .decodingError(let error):
            return "Decoding error: \(error.localizedDescription)"
        case .encodingError(let error):
            return "Encoding error: \(error.localizedDescription)"
        }
    }
}

// MARK: - Request Models

struct QueryRequest: Codable {
    let question: String
    let language: String?
    let contextType: String?
    let maxContextChunks: Int
    let similarityThreshold: Double
}

struct IndexRequest: Codable {
    let directoryPath: String
    let recursive: Bool
    let filePatterns: [String]?
}

struct CodeGenerationRequest: Codable {
    let problemDescription: String
    let language: String?
    let framework: String?
}

// MARK: - Response Models

struct QueryResponse: Codable {
    let answer: String
    let retrievedContext: [RetrievedContext]
    let metadata: [String: String]
}

struct RetrievedContext: Codable {
    let content: String
    let filePath: String
    let lineStart: Int
    let lineEnd: Int
    let score: Double
    let language: String
    let chunkType: String
}

struct SystemStatusResponse: Codable {
    let status: String
    let components: [String: Bool]
    let monitoringActive: Bool
    let version: String
}

struct IndexStatsResponse: Codable {
    let indexedFiles: Int
    let totalChunks: Int
    let languages: [String]
}
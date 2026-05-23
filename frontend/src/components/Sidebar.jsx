import { useState, useRef } from "react";
import { UploadCloud, FileText, Trash2, X, AlertCircle } from "lucide-react";
import axios from "axios";

export default function Sidebar() {
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState(null);
    const fileInputRef = useRef(null);

    const handleFileChange = async (e) => {
        const selectedFiles = Array.from(e.target.files);
        if (selectedFiles.length === 0) return;

        setUploading(true);
        setError(null);

        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append("files", file);
        });

        try {
            const res = await axios.post("http://localhost:8000/api/upload", formData, {
                headers: { "Content-Type": "multipart/form-data" }
            });

            setFiles(prev => [...prev, ...res.data.processed_files]);
        } catch (err) {
            setError(err.response?.data?.detail || "Upload failed");
        } finally {
            setUploading(false);
            // Reset input
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    };

    const handleReset = async () => {
        try {
            await axios.delete("http://localhost:8000/api/system/reset");
            setFiles([]);
            window.location.reload(); // Quick refresh to clear local chat state as well
        } catch (err) {
            setError("Reset failed");
        }
    };

    return (
        <div className="w-80 border-r border-gray-200 bg-white flex flex-col h-full shadow-sm">
            <div className="p-6 border-b border-gray-200">
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-1">
                    RAG Assistant
                </h1>
                <p className="text-sm text-gray-500">Ask questions about your docs</p>
            </div>

            <div className="p-4 flex-1 overflow-y-auto">
                <div
                    className="border-2 border-dashed border-gray-300 rounded-xl p-6 mb-6 text-center cursor-pointer hover:bg-gray-50 hover:border-blue-400 transition-colors"
                    onClick={() => fileInputRef.current?.click()}
                >
                    <input
                        type="file"
                        multiple
                        className="hidden"
                        ref={fileInputRef}
                        onChange={handleFileChange}
                        accept=".pdf,.docx,.txt"
                    />
                    <UploadCloud className="mx-auto h-8 w-8 text-blue-500 mb-2" />
                    <p className="text-sm font-medium text-gray-700">Upload Knowledge</p>
                    <p className="text-xs text-gray-500 mt-1">PDF, DOCX, TXT</p>

                    {uploading && (
                        <div className="mt-3 text-xs text-blue-600 flex items-center justify-center">
                            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600 mr-2"></div>
                            Processing...
                        </div>
                    )}
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-50 text-red-700 text-xs rounded flex items-start">
                        <AlertCircle className="w-4 h-4 mr-2 shrink-0 border-red-500" />
                        <span>{error}</span>
                    </div>
                )}

                <div className="mb-4">
                    <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Knowledge Base</h3>

                    {files.length === 0 ? (
                        <div className="text-sm text-gray-400 italic px-2">No documents uploaded yet.</div>
                    ) : (
                        <div className="space-y-2">
                            {files.map((file, idx) => (
                                <div key={idx} className="flex items-center p-2 rounded bg-gray-50 border border-gray-100">
                                    <FileText className="w-4 h-4 text-gray-400 mr-2 shrink-0" />
                                    <span className="text-sm text-gray-700 truncate" title={file}>{file}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            <div className="p-4 border-t border-gray-200">
                <button
                    onClick={handleReset}
                    className="w-full py-2 px-4 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors text-sm font-medium flex items-center justify-center"
                >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Clear System
                </button>
            </div>
        </div>
    );
}

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";

export default function ChatArea() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);

    const [sessionId] = useState(() => {
        const saved = localStorage.getItem('chat_session_id');
        if (saved) return saved;
        const newId = Math.random().toString(36).substring(7);
        localStorage.setItem('chat_session_id', newId);
        return newId;
    });

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const response = await axios.get(`http://localhost:8000/api/chat/history?session_id=${sessionId}`);
                if (response.data && response.data.length > 0) {
                    const mapped = response.data.map(m => ({
                        role: m.role === 'human' ? 'user' : 'assistant',
                        content: m.content,
                        sources: m.sources ? (typeof m.sources === 'string' ? JSON.parse(m.sources) : m.sources) : null
                    }));
                    setMessages(mapped);
                } else {
                    setMessages([{ role: "assistant", content: "Hello! I am your AI assistant. Upload some documents and ask me anything about them." }]);
                }
            } catch (err) {
                console.error("Failed to fetch history:", err);
                setMessages([{ role: "assistant", content: "Hello! I am your AI assistant. Upload some documents and ask me anything about them." }]);
            }
        };
        fetchHistory();
    }, [sessionId]);

    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMessage = input.trim();
        setInput("");

        // Add user message
        setMessages(prev => [...prev, { role: "user", content: userMessage }]);
        setLoading(true);

        try {
            const res = await axios.post("http://localhost:8000/api/chat", {
                message: userMessage,
                session_id: sessionId
            });

            setMessages(prev => [...prev, {
                role: "assistant",
                content: res.data.answer,
                sources: res.data.sources
            }]);
        } catch (err) {
            setMessages(prev => [...prev, {
                role: "assistant",
                content: "Sorry, I encountered an error. Please try again."
            }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-white relative">
            {/* Header */}
            <div className="h-16 border-b border-gray-200 flex items-center px-6 shadow-sm z-10 bg-white">
                <h2 className="text-lg font-semibold text-gray-800">Chat Session</h2>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50">
                <AnimatePresence>
                    {messages.map((msg, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div className={`flex max-w-[80%] ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-md ${msg.role === "user" ? "bg-blue-600 ml-3" : "bg-indigo-600 mr-3"
                                    }`}>
                                    {msg.role === "user" ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
                                </div>

                                <div className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                                    <div className={`px-5 py-3 rounded-2xl shadow-sm ${msg.role === "user"
                                        ? "bg-blue-600 text-white rounded-tr-none"
                                        : "bg-white border border-gray-100 text-gray-800 rounded-tl-none"
                                        }`}>
                                        {msg.role === "user" ? (
                                            <p className="whitespace-pre-wrap">{msg.content}</p>
                                        ) : (
                                            <div className="prose prose-sm prose-slate max-w-none">
                                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                                            </div>
                                        )}
                                    </div>

                                    {/* Sources Accordion/List for AI */}
                                    {msg.sources && msg.sources.length > 0 && (
                                        <div className="mt-2 ml-2">
                                            <details className="text-xs text-gray-500 group">
                                                <summary className="cursor-pointer hover:text-indigo-600 transition-colors list-none flex items-center font-medium">
                                                    <span className="mr-1 text-indigo-400">❖</span> View {msg.sources.length} Sources
                                                </summary>
                                                <div className="mt-2 space-y-2 bg-white p-3 rounded-lg border border-gray-200 shadow-sm max-w-lg">
                                                    {msg.sources.map((src, i) => (
                                                        <div key={i} className="bg-slate-50 p-2 rounded overflow-hidden">
                                                            <p className="text-xs font-semibold text-gray-700 mb-1">
                                                                Source: {src.metadata.source || "Unknown"}
                                                            </p>
                                                            <p className="text-[10px] text-gray-500 line-clamp-3">
                                                                {src.content}
                                                            </p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </details>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {loading && (
                    <motion.div
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                        className="flex justify-start"
                    >
                        <div className="flex items-center bg-white border border-gray-200 rounded-2xl rounded-tl-none px-5 py-3 shadow-sm ml-11">
                            <Loader2 className="w-4 h-4 animate-spin text-indigo-600 mr-2" />
                            <span className="text-sm font-medium text-gray-500">Thinking...</span>
                        </div>
                    </motion.div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Form */}
            <div className="p-4 bg-white border-t border-gray-200">
                <form onSubmit={handleSend} className="max-w-4xl mx-auto relative flex items-center">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={loading}
                        placeholder="Send a message to the AI..."
                        className="w-full bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-xl focus:ring-blue-500 focus:border-blue-500 block p-4 pr-12 shadow-sm transition-shadow hover:shadow-md disabled:opacity-50"
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || loading}
                        className="absolute right-2 p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </form>
                <p className="text-center text-[10px] text-gray-400 mt-2">
                    AI can make mistakes. Verify important facts from the source documents.
                </p>
            </div>
        </div>
    );
}

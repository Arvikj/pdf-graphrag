import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Bot, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const ChatInterface = () => {
    const [messages, setMessages] = useState([
        { id: 1, sender: 'system', text: 'Hello! I have analyzed your PDF. Ask me anything about it.' }
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages, isTyping]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMsg = { id: Date.now(), sender: 'user', text: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsTyping(true);

        try {
            const response = await axios.post('/api/chat', { message: userMsg.text });
            const responseMsg = {
                id: Date.now() + 1,
                sender: 'system',
                text: response.data.response
            };
            setMessages(prev => [...prev, responseMsg]);
        } catch (error) {
            console.error('Chat error:', error);
            const errorMsg = {
                id: Date.now() + 1,
                sender: 'system',
                text: `Error: ${error.response?.data?.detail || 'Failed to get response. Make sure Neo4j and Ollama are running.'}`
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div className="flex flex-col h-[600px] bg-white dark:bg-dark-card rounded-3xl shadow-xl overflow-hidden border border-gray-100 dark:border-gray-700">
            {/* Header */}
            <div className="p-4 border-b border-gray-100 dark:border-gray-700 bg-white/50 dark:bg-dark-card/50 backdrop-blur-md sticky top-0 z-10">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary to-secondary flex items-center justify-center text-white shadow-lg">
                        <Bot size={20} />
                    </div>
                    <div>
                        <div>
                            <h3 className="font-bold text-gray-800 dark:text-white">AI Assistant</h3>
                        </div>
                    </div>
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.map((msg) => (
                    <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex gap-4 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
                    >
                        <div className={`
              w-8 h-8 rounded-full flex items-center justify-center shrink-0
              ${msg.sender === 'user' ? 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300' : 'bg-primary/10 text-primary'}
            `}>
                            {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
                        </div>

                        <div className={`
              max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed shadow-sm
              ${msg.sender === 'user'
                                ? 'bg-primary text-white rounded-tr-none'
                                : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-tl-none'}
            `}>
                            {msg.text}
                        </div>
                    </motion.div>
                ))}

                {isTyping && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex gap-4"
                    >
                        <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0">
                            <Bot size={16} />
                        </div>
                        <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-2xl rounded-tl-none flex gap-1 items-center">
                            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                        </div>
                    </motion.div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-white dark:bg-dark-card border-t border-gray-100 dark:border-gray-700">
                <form onSubmit={handleSend} className="relative flex items-center gap-2">
                    <button
                        type="button"
                        className="p-3 text-gray-400 hover:text-primary transition-colors rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800"
                    >
                        <Paperclip size={20} />
                    </button>

                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask a question about the document..."
                        className="flex-1 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all placeholder:text-gray-400"
                    />

                    <button
                        type="submit"
                        disabled={!input.trim() || isTyping}
                        className="p-3 bg-primary text-white rounded-xl hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-primary/30"
                    >
                        <Send size={20} />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatInterface;

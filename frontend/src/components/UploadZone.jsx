import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone'; // We need to install this or implement custom logic. Let's use custom logic to avoid extra deps if possible, but react-dropzone is standard. I'll implement a custom one to save install time.
import { UploadCloud, File, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ProcessingStatus from './ProcessingStatus';
import axios from 'axios';

const UploadZone = ({ onUploadComplete }) => {
    const [isDragOver, setIsDragOver] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState(null);

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setIsDragOver(false);
    };

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setIsDragOver(false);
        setError(null);

        const files = e.dataTransfer.files;
        if (files.length > 1) {
            setError("Please upload only one PDF at a time.");
            return;
        }

        const file = files[0];
        if (file && file.type === "application/pdf") {
            startUpload(file);
        } else {
            setError("Only PDF files are allowed.");
        }
    }, []);

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            startUpload(file);
        }
    };

    const [isUploadFinished, setIsUploadFinished] = useState(false);

    const startUpload = async (file) => {
        setIsProcessing(true);
        setIsUploadFinished(false);

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Real API call
            // Use relative path so Vite proxy handles it (works for both localhost and dev tunnels)
            await axios.post('/api/upload', formData);
            console.log("Upload and processing complete");
            setIsUploadFinished(true);
        } catch (err) {
            console.error("Upload failed", err);
            setError("Upload failed. Please try again.");
            setIsProcessing(false);
        }
    };

    const handleProcessingComplete = () => {
        setIsProcessing(false);
        onUploadComplete();
    };

    if (isProcessing) {
        return <ProcessingStatus onComplete={handleProcessingComplete} isFinished={isUploadFinished} />;
    }

    return (
        <div className="w-full max-w-2xl mx-auto mt-10">
            <motion.div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                animate={{
                    scale: isDragOver ? 1.02 : 1,
                    borderColor: isDragOver ? '#3B82F6' : '#E5E7EB',
                    backgroundColor: isDragOver ? 'rgba(59, 130, 246, 0.05)' : 'transparent'
                }}
                className={`
          relative border-2 border-dashed rounded-3xl p-12 text-center transition-colors duration-300
          ${isDragOver ? 'border-primary' : 'border-gray-300 dark:border-gray-600'}
          bg-white/50 dark:bg-dark-card/50 backdrop-blur-sm
        `}
            >
                <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileSelect}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />

                <div className="flex flex-col items-center gap-6 pointer-events-none">
                    <motion.div
                        animate={{ y: isDragOver ? -10 : 0 }}
                        className="w-20 h-20 bg-blue-50 dark:bg-blue-900/30 rounded-full flex items-center justify-center text-primary"
                    >
                        <UploadCloud size={40} />
                    </motion.div>

                    <div>
                        <h3 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">
                            Drop your PDF here
                        </h3>
                        <p className="text-gray-500 dark:text-gray-400">
                            or click to browse
                        </p>
                    </div>

                    <div className="flex items-center gap-2 text-sm text-gray-400 bg-gray-100 dark:bg-gray-800 px-4 py-2 rounded-full">
                        <File size={14} />
                        <span>Supports PDF only (Max 10MB)</span>
                    </div>
                </div>
            </motion.div>

            <AnimatePresence>
                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl flex items-center gap-3"
                    >
                        <X size={20} />
                        {error}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default UploadZone;

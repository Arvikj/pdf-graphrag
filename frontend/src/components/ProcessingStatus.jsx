import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Circle, Loader2, FileText, BrainCircuit, Network, Check } from 'lucide-react';

const steps = [
    { id: 1, label: 'Uploading PDF', icon: FileText },
    { id: 2, label: 'Parsing Text (OCR)', icon: Loader2 },
    { id: 3, label: 'Extracting Entities', icon: BrainCircuit },
    { id: 4, label: 'Building Graph', icon: Network },
    { id: 5, label: 'Ready!', icon: CheckCircle2 },
];

const ProcessingStatus = ({ onComplete, isFinished }) => {
    const [currentStep, setCurrentStep] = useState(1);

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentStep((prev) => {
                // If we are at the last step (Ready), don't do anything
                if (prev >= steps.length) {
                    clearInterval(timer);
                    return prev;
                }

                // If we are at the step before Ready (Building Graph), wait for isFinished
                if (prev === steps.length - 1) {
                    if (isFinished) {
                        return prev + 1; // Move to Ready
                    }
                    return prev; // Wait here
                }

                // Otherwise, advance normally
                return prev + 1;
            });
        }, 2000); // 2 seconds per step

        return () => clearInterval(timer);
    }, [isFinished]);

    // Watch for isFinished to force completion if we're stuck waiting
    useEffect(() => {
        if (isFinished && currentStep === steps.length - 1) {
            setCurrentStep(steps.length);
        }
    }, [isFinished, currentStep]);

    // When we reach the last step, trigger onComplete after a delay
    useEffect(() => {
        if (currentStep === steps.length) {
            const timeout = setTimeout(onComplete, 1000);
            return () => clearTimeout(timeout);
        }
    }, [currentStep, onComplete]);

    return (
        <div className="w-full max-w-md mx-auto bg-white dark:bg-dark-card rounded-2xl p-8 shadow-xl border border-gray-100 dark:border-gray-700">
            <h3 className="text-xl font-bold mb-6 text-center text-gray-800 dark:text-white">Processing Document</h3>
            <div className="space-y-6">
                {steps.map((step) => {
                    const Icon = step.icon;
                    const isCompleted = currentStep > step.id;
                    const isCurrent = currentStep === step.id;
                    const isPending = currentStep < step.id;

                    return (
                        <motion.div
                            key={step.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className={`flex items-center gap-4 ${isPending ? 'opacity-40' : 'opacity-100'}`}
                        >
                            <div className="relative">
                                <motion.div
                                    initial={false}
                                    animate={{
                                        scale: isCurrent ? 1.2 : 1,
                                        backgroundColor: isCompleted ? '#10B981' : isCurrent ? '#3B82F6' : '#E5E7EB',
                                        borderColor: isCompleted ? '#10B981' : isCurrent ? '#3B82F6' : '#E5E7EB',
                                    }}
                                    className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors duration-300`}
                                >
                                    {isCompleted ? (
                                        <Check size={16} className="text-white" />
                                    ) : isCurrent ? (
                                        <Icon size={16} className="text-white animate-spin-slow" />
                                    ) : (
                                        <Circle size={16} className="text-gray-400" />
                                    )}
                                </motion.div>
                                {/* Connecting Line */}
                                {step.id !== steps.length && (
                                    <div className={`absolute top-8 left-1/2 -translate-x-1/2 w-0.5 h-6 ${isCompleted ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'}`} />
                                )}
                            </div>

                            <div className="flex-1">
                                <p className={`font-medium ${isCurrent ? 'text-primary dark:text-blue-400' : isCompleted ? 'text-green-600 dark:text-green-400' : 'text-gray-500'}`}>
                                    {step.label}
                                </p>
                                {isCurrent && (
                                    <motion.div
                                        layoutId="active-pill"
                                        className="h-1 w-12 bg-primary/20 rounded-full mt-1 overflow-hidden"
                                    >
                                        <motion.div
                                            className="h-full bg-primary"
                                            animate={{ x: ['-100%', '100%'] }}
                                            transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                                        />
                                    </motion.div>
                                )}
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
};

export default ProcessingStatus;

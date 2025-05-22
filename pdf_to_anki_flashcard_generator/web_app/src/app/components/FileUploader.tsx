import { useState, useRef, ChangeEvent } from "react";

interface FileUploaderProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  isProcessing: boolean;
}

export const FileUploader = ({ file, onFileChange, isProcessing }: FileUploaderProps) => {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    if (files && files[0]) {
      const selectedFile = files[0];
      if (selectedFile.type === "application/pdf") {
        onFileChange(selectedFile);
      } else {
        alert("Bitte wählen Sie eine PDF-Datei aus.");
        onFileChange(null);
      }
    }
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    handleFiles(e.target.files);
  };

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleClick = () => {
    if (inputRef.current) {
      inputRef.current.click();
    }
  };

  const handleRemoveFile = () => {
    onFileChange(null);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  return (
    <div className="mb-6">
      <label className="block text-gray-700 text-sm font-bold mb-2">
        PDF-Datei
      </label>
      
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center ${
          dragActive 
            ? "border-blue-500 bg-blue-50" 
            : file 
              ? "border-green-500 bg-green-50" 
              : "border-gray-300 hover:border-gray-400"
        } ${isProcessing ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={!isProcessing && !file ? handleClick : undefined}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          onChange={handleChange}
          className="hidden"
          disabled={isProcessing}
        />
        
        {file ? (
          <div className="flex flex-col items-center">
            <svg 
              className="w-10 h-10 text-green-500 mb-2" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="2" 
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-sm font-medium text-gray-800">{file.name}</p>
            <p className="text-xs text-gray-500 mt-1">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
            {!isProcessing && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemoveFile();
                }}
                className="mt-3 text-xs text-red-600 hover:text-red-800 font-medium"
              >
                Entfernen
              </button>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <svg 
              className="w-10 h-10 text-gray-400 mb-2" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="2" 
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="text-sm font-medium text-gray-700">
              Klicken Sie oder ziehen Sie eine Datei hierher
            </p>
            <p className="text-xs text-gray-500 mt-1">
              PDF-Dateien bis zu 50MB
            </p>
          </div>
        )}
      </div>
    </div>
  );
}; 
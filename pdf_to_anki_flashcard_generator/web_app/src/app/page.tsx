"use client";

import { useState, useRef } from "react";
import { FileUploader } from "./components/FileUploader";
import { FormSettings } from "./components/FormSettings";
import { ProcessingStatus } from "./components/ProcessingStatus";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [deckName, setDeckName] = useState<string>("Generated Anki Deck");
  const [maxChars, setMaxChars] = useState<number>(1800);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [status, setStatus] = useState<{
    type: "idle" | "processing" | "success" | "error";
    message: string;
  }>({
    type: "idle",
    message: "",
  });

  const handleFileChange = (selectedFile: File | null) => {
    setFile(selectedFile);
    if (selectedFile && !deckName.includes(selectedFile.name)) {
      const baseName = selectedFile.name.replace(/\.[^/.]+$/, "");
      setDeckName(baseName);
    }
  };

  const handleProcessPdf = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setStatus({
        type: "error",
        message: "Bitte wählen Sie eine PDF-Datei aus.",
      });
      return;
    }

    setIsProcessing(true);
    setStatus({
      type: "processing",
      message: "PDF wird verarbeitet. Bitte warten...",
    });

    const formData = new FormData();
    formData.append("file", file);
    formData.append("deckName", deckName);
    formData.append("maxChars", maxChars.toString());

    try {
      const response = await fetch("http://localhost:5000/api/process-pdf", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Fehler bei der Verarbeitung der PDF-Datei");
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get("Content-Disposition");
      let filename = "anki-deck.apkg";
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1];
        }
      }

      // Create a download link for the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setStatus({
        type: "success",
        message: "Anki-Deck erfolgreich erstellt und heruntergeladen!",
      });
    } catch (error) {
      console.error("Error:", error);
      setStatus({
        type: "error",
        message: `Fehler: ${error instanceof Error ? error.message : "Unbekannter Fehler"}`,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-6 sm:p-12 md:p-24">
      <div className="z-10 w-full max-w-4xl items-center justify-center text-sm flex flex-col">
        <h1 className="text-4xl font-bold mb-8 text-center">Anki Karteikarten Generator</h1>
        <p className="text-lg text-center text-gray-600 mb-12">
          Laden Sie eine PDF-Datei hoch und erstellen Sie automatisch Anki-Karteikarten mit KI-Unterstützung.
        </p>
        
        <div className="w-full max-w-md bg-white p-8 rounded-xl shadow-lg">
          <form onSubmit={handleProcessPdf}>
            <FileUploader 
              file={file} 
              onFileChange={handleFileChange} 
              isProcessing={isProcessing}
            />
            
            <FormSettings
              deckName={deckName}
              setDeckName={setDeckName}
              maxChars={maxChars}
              setMaxChars={setMaxChars}
              isProcessing={isProcessing}
            />
            
            <div className="mt-8">
              <button
                type="submit"
                disabled={!file || isProcessing}
                className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {isProcessing ? "Verarbeitung läuft..." : "PDF verarbeiten"}
              </button>
            </div>
          </form>
        </div>
        
        <ProcessingStatus status={status} />
      </div>
    </main>
  );
}

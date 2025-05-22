import { ChangeEvent } from "react";

interface FormSettingsProps {
  deckName: string;
  setDeckName: (name: string) => void;
  maxChars: number;
  setMaxChars: (chars: number) => void;
  isProcessing: boolean;
}

export const FormSettings = ({
  deckName,
  setDeckName,
  maxChars,
  setMaxChars,
  isProcessing,
}: FormSettingsProps) => {
  const handleDeckNameChange = (e: ChangeEvent<HTMLInputElement>) => {
    setDeckName(e.target.value);
  };

  const handleMaxCharsChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value);
    if (!isNaN(value) && value > 0) {
      setMaxChars(value);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label 
          htmlFor="deckName" 
          className="block text-gray-700 text-sm font-bold mb-2"
        >
          Deck-Name
        </label>
        <input
          id="deckName"
          type="text"
          value={deckName}
          onChange={handleDeckNameChange}
          disabled={isProcessing}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
          placeholder="Name des Anki-Decks"
          aria-label="Deck Name"
        />
      </div>

      <div>
        <label 
          htmlFor="maxChars" 
          className="block text-gray-700 text-sm font-bold mb-2"
        >
          Maximale Zeichen pro Chunk
        </label>
        <div className="flex items-center">
          <input
            id="maxChars"
            type="range"
            min="500"
            max="3000"
            step="100"
            value={maxChars}
            onChange={handleMaxCharsChange}
            disabled={isProcessing}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            aria-label="Maximum characters per chunk"
          />
          <span className="ml-3 text-sm text-gray-600 w-16">{maxChars}</span>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Ein niedrigerer Wert erzeugt mehr präzise Karteikarten, ein höherer Wert reduziert die Anzahl der Karten.
        </p>
      </div>
    </div>
  );
}; 
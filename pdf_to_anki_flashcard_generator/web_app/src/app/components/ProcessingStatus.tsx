interface ProcessingStatusProps {
  status: {
    type: "idle" | "processing" | "success" | "error";
    message: string;
  };
}

export const ProcessingStatus = ({ status }: ProcessingStatusProps) => {
  if (status.type === "idle" || status.message === "") {
    return null;
  }

  const statusStyles = {
    processing: "bg-blue-50 text-blue-800 border-blue-200",
    success: "bg-green-50 text-green-800 border-green-200",
    error: "bg-red-50 text-red-800 border-red-200",
  };

  const iconMap = {
    processing: (
      <svg
        className="animate-spin h-5 w-5 text-blue-600"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        ></circle>
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
      </svg>
    ),
    success: (
      <svg
        className="h-5 w-5 text-green-600"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M5 13l4 4L19 7"
        />
      </svg>
    ),
    error: (
      <svg
        className="h-5 w-5 text-red-600"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
    ),
  };

  return (
    <div
      className={`mt-8 p-4 border rounded-lg flex items-start max-w-md ${
        statusStyles[status.type]
      }`}
      role="alert"
      aria-live="polite"
    >
      <div className="flex-shrink-0 mr-3 mt-0.5">{iconMap[status.type]}</div>
      <div className="flex-grow">
        <p className="text-sm font-medium">{status.message}</p>
      </div>
    </div>
  );
}; 
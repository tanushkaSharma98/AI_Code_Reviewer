import React from "react";

type Props = {
  status: string;
  downloadUrl?: string;
  onDownload?: () => void;
};

const StatusDisplay: React.FC<Props> = ({ status, downloadUrl, onDownload }) => (
  <div className="mt-6 p-4 bg-gray-100 rounded">
    <div className="font-semibold mb-2">Status:</div>
    <div className="mb-2">
      <span className="font-mono">{status}</span>
      {status === "complete" && downloadUrl && (
        <>
          <br />
          <button
            className="mt-2 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
            onClick={onDownload}
          >
            Download Review ZIP
          </button>
        </>
      )}
    </div>
  </div>
);

export default StatusDisplay; 
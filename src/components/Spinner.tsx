import React from "react";

const Spinner: React.FC = () => (
  <div className="flex justify-center items-center">
    <div className="w-6 h-6 border-4 border-blue-400 border-t-transparent rounded-full animate-spin" />
  </div>
);

export default Spinner; 
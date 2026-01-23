import React, { useState } from 'react';
import { AlertCircle, CheckCircle, X } from 'lucide-react';

interface ProposedAction {
  id: string;
  tool_name: string;
  description: string;
  parameters: Record<string, any>;
  safety_assessment: {
    risk_level: 'low' | 'medium' | 'high';
    concerns: string[];
  };
}

interface ActionConfirmationProps {
  action: ProposedAction;
  onConfirm: () => void;
  onReject: () => void;
  onClose: () => void;
}

export const ActionConfirmation: React.FC<ActionConfirmationProps> = ({
  action,
  onConfirm,
  onReject,
  onClose,
}) => {
  const [isConfirming, setIsConfirming] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'text-green-600 bg-green-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'high':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const handleConfirm = async () => {
    setIsConfirming(true);
    try {
      await onConfirm();
    } finally {
      setIsConfirming(false);
    }
  };

  const handleReject = async () => {
    setIsRejecting(true);
    try {
      await onReject();
    } finally {
      setIsRejecting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-6 h-6 text-yellow-500" />
            <h2 className="text-xl font-semibold text-gray-800">Confirm Action</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Description */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Action Description</h3>
            <p className="text-gray-600">{action.description}</p>
          </div>

          {/* Tool Name */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Tool</h3>
            <div className="inline-flex px-3 py-1 bg-primary-100 text-primary-700 rounded-lg text-sm font-medium">
              {action.tool_name}
            </div>
          </div>

          {/* Parameters */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Parameters</h3>
            <div className="bg-gray-50 rounded-lg p-4 overflow-x-auto">
              <pre className="text-sm text-gray-800">
                {JSON.stringify(action.parameters, null, 2)}
              </pre>
            </div>
          </div>

          {/* Safety Assessment */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">Safety Assessment</h3>

            <div className="space-y-3">
              {/* Risk Level */}
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-600">Risk Level:</span>
                <span className={`px-3 py-1 rounded-lg text-sm font-medium ${getRiskColor(action.safety_assessment.risk_level)}`}>
                  {action.safety_assessment.risk_level.toUpperCase()}
                </span>
              </div>

              {/* Concerns */}
              {action.safety_assessment.concerns.length > 0 && (
                <div>
                  <div className="text-sm text-gray-600 mb-2">Potential Concerns:</div>
                  <ul className="space-y-2">
                    {action.safety_assessment.concerns.map((concern, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <AlertCircle className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-700">{concern}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Warning Box */}
          {action.safety_assessment.risk_level === 'high' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-red-800 mb-1">High Risk Action</h4>
                  <p className="text-sm text-red-700">
                    This action has been assessed as high risk. Please review carefully before proceeding.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 flex items-center justify-end space-x-3">
          <button
            onClick={handleReject}
            disabled={isConfirming || isRejecting}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRejecting ? 'Rejecting...' : 'Reject'}
          </button>
          <button
            onClick={handleConfirm}
            disabled={isConfirming || isRejecting}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isConfirming ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Confirming...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>Confirm & Execute</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ActionConfirmation;

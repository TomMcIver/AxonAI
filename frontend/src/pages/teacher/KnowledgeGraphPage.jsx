import React, { useState } from 'react';
import Layout from '../../components/Layout';
import KnowledgeGraph from '../../components/KnowledgeGraph';

const SUBJECTS = ['Mathematics', 'Biology'];

export default function KnowledgeGraphPage() {
  const [subject, setSubject] = useState('Mathematics');

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#1F2937]">Knowledge Graph</h1>
        <p className="text-[#6B7280]">Explore concept prerequisites and dependencies</p>
      </div>

      <div className="flex gap-2 mb-6">
        {SUBJECTS.map(s => (
          <button
            key={s}
            onClick={() => setSubject(s)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              subject === s
                ? 'bg-[#1E2761] text-white'
                : 'bg-white text-[#6B7280] border border-[#E2E8F0] hover:bg-[#F1F5F9]'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      <KnowledgeGraph subject={subject} />
    </Layout>
  );
}

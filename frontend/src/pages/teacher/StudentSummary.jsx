import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import { BASE_URL } from '../../api/axonai';
import DashboardShell from '../../components/DashboardShell';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';

export default function StudentSummary() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    console.log('Fetching student summary for student:', id);

    fetch(`${BASE_URL}/student/${id}/summary`, { signal: controller.signal })
      .then(res => {
        if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
        return res.json();
      })
      .then(responseData => {
        console.log('API Response:', responseData);
        setData(responseData);
        setLoading(false);
      })
      .catch(err => {
        if (err.name === 'AbortError') return;
        console.error('Failed to fetch:', err);
        setError(err.message);
        setLoading(false);
      });

    return () => controller.abort();
  }, [id, retryCount]);

  if (loading) {
    return (
      <DashboardShell subtitle="Student profile">
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner message="Loading student profile..." />
        </div>
      </DashboardShell>
    );
  }

  if (error) {
    return (
      <DashboardShell subtitle="Student profile">
        <div className="flex items-center justify-center py-16">
          <ErrorState message={error} onRetry={() => setRetryCount(c => c + 1)} />
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell subtitle="Student · summary">
      <div className="space-y-6 max-w-2xl mx-auto px-4">
        {/* ── Navigation ── */}
        <div className="flex items-center justify-between gap-3">
          <button
            className="axon-btn axon-btn-quiet"
            onClick={() => navigate(-1)}
          >
            ← Back
          </button>
        </div>

        {/* ── Class Cards Grid ── */}
        {data?.classes && data.classes.length > 0 && (
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2">
            {data.classes.map((cls) => {
              console.log('Rendering class:', cls.class_name, 'score:', cls.overall_score);
              console.log('Top 3 mastered:', cls.top_3_mastered);
              console.log('Bottom 3 struggling:', cls.bottom_3_struggling);

              const score = Math.min(100, Math.max(0, cls.overall_score || 0));

              return (
                <div
                  key={cls.class_name}
                  style={{
                    background: 'rgba(23, 16, 8, 0.72)',
                    backdropFilter: 'blur(16px) saturate(180%)',
                    WebkitBackdropFilter: 'blur(16px) saturate(180%)',
                    border: '1px solid rgba(251, 191, 36, 0.15)',
                    borderRadius: 16,
                    padding: '20px 24px',
                  }}
                >
                  {/* Class name header */}
                  <h3
                    style={{
                      color: 'rgba(253, 230, 138, 0.9)',
                      fontWeight: 600,
                      fontSize: '0.9rem',
                      marginBottom: 12,
                    }}
                  >
                    {cls.class_name}
                  </h3>

                  {/* Overall score bar */}
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>
                        Overall score
                      </span>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#2dd4bf' }}>
                        {Math.round(score)}%
                      </span>
                    </div>
                    <div
                      style={{
                        height: 6,
                        borderRadius: 9999,
                        background: 'rgba(255,255,255,0.1)',
                        overflow: 'hidden',
                      }}
                    >
                      <div
                        style={{
                          height: '100%',
                          width: `${score}%`,
                          background: '#14b8a6',
                          borderRadius: 9999,
                          transition: 'width 0.5s ease-out',
                        }}
                      />
                    </div>
                  </div>

                  {/* Top 3 Mastered */}
                  {cls.top_3_mastered && cls.top_3_mastered.length > 0 && (
                    <div style={{ marginBottom: 12 }}>
                      <p
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 600,
                          color: 'rgba(255,255,255,0.45)',
                          textTransform: 'uppercase',
                          letterSpacing: '0.12em',
                          marginBottom: 8,
                        }}
                      >
                        Top 3 Mastered
                      </p>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {cls.top_3_mastered.map((concept) => (
                          <div
                            key={concept.concept_name}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 8,
                              padding: '6px 10px',
                              borderRadius: 8,
                              background: 'rgba(6, 78, 59, 0.4)',
                              border: '1px solid rgba(52, 211, 153, 0.3)',
                            }}
                          >
                            <CheckCircle2 size={14} style={{ color: '#34d399', flexShrink: 0 }} />
                            <span
                              style={{
                                flex: 1,
                                fontSize: '0.78rem',
                                color: '#6ee7b7',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {concept.concept_name}
                            </span>
                            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#34d399', flexShrink: 0 }}>
                              {Math.round(concept.mastery_score)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Bottom 3 Struggling */}
                  {cls.bottom_3_struggling && cls.bottom_3_struggling.length > 0 && (
                    <div>
                      <p
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 600,
                          color: 'rgba(255,255,255,0.45)',
                          textTransform: 'uppercase',
                          letterSpacing: '0.12em',
                          marginBottom: 8,
                        }}
                      >
                        Bottom 3 Struggling
                      </p>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {cls.bottom_3_struggling.map((concept) => (
                          <div
                            key={concept.concept_name}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 8,
                              padding: '6px 10px',
                              borderRadius: 8,
                              background: 'rgba(127, 29, 29, 0.4)',
                              border: '1px solid rgba(248, 113, 113, 0.3)',
                            }}
                          >
                            <AlertCircle size={14} style={{ color: '#f87171', flexShrink: 0 }} />
                            <span
                              style={{
                                flex: 1,
                                fontSize: '0.78rem',
                                color: '#fca5a5',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {concept.concept_name}
                            </span>
                            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f87171', flexShrink: 0 }}>
                              {Math.round(concept.mastery_score)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ── Action Buttons ── */}
        <div className="flex gap-3">
          <button
            className="flex-1 axon-btn axon-btn-primary"
            onClick={() => navigate(`/teacher/student/${id}`)}
          >
            Deep dive
          </button>
        </div>
      </div>
    </DashboardShell>
  );
}

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { loadStudentDashboardBundle } from '../../api/primedRequests';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import DashboardShell from '../../components/DashboardShell';
import KnowledgeGraphNew from '../../components/KnowledgeGraphNew';
import { useTimedProgress } from '../../hooks/useTimedProgress';

const DASH_FILL_MS = 4200;

export default function StudentKnowledgeGraphPage() {
  const { id } = useParams();
  const studentId = id || 1;

  const [dashboard, setDashboard] = useState(null);
  const [mastery, setMastery] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [barEpoch, setBarEpoch] = useState(0);
  const progress = useTimedProgress(DASH_FILL_MS, barEpoch);
  const studentIdFirst = useRef(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    loadStudentDashboardBundle(studentId)
      .then(({ dashboard: d, mastery: m, graphData: g }) => {
        setDashboard(d);
        setMastery(m);
        setGraphData(g);
        setLoading(false);
      })
      .catch(e => {
        setError(e.message);
        setLoading(false);
      });
  }, [studentId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (studentIdFirst.current) {
      studentIdFirst.current = false;
      return;
    }
    setBarEpoch((e) => e + 1);
  }, [studentId]);

  const concepts = mastery?.concepts || [];
  const n = (x) => (typeof x === 'number' && x > 1 ? x / 100 : x) || 0;
  const masteryMapForGraph = useMemo(
    () =>
      concepts.reduce((map, c) => {
        if (c.concept_id != null) {
          const raw = c.mastery_score ?? null;
          map[c.concept_id] = raw !== null ? n(raw) : null;
        }
        return map;
      }, {}),
    [concepts],
  );

  const hasLearningGraph = graphData && (graphData.concepts || []).length > 0;

  const dataReady = Boolean(dashboard) && !loading;
  const barComplete = progress >= 99.9;
  const showMain = dataReady && barComplete;
  const waitingOnApi = progress >= 99.9 && !dataReady && !error;

  const studentName = dashboard?.student?.first_name;

  if (error) {
    return (
      <DashboardShell subtitle="Student · Learning map">
        <div className="flex items-center justify-center py-16">
          <ErrorState
            message={error}
            onRetry={() => {
              setBarEpoch((e) => e + 1);
              load();
            }}
          />
        </div>
      </DashboardShell>
    );
  }

  if (!showMain) {
    return (
      <DashboardShell subtitle="Student · Learning map">
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner
            message={
              waitingOnApi
                ? 'Still loading…'
                : dataReady
                  ? 'Opening your learning map…'
                  : 'Loading your learning map...'
            }
            progress={progress}
          />
        </div>
      </DashboardShell>
    );
  }

  if (!dashboard) {
    return (
      <DashboardShell subtitle="Student · Learning map">
        <div className="flex items-center justify-center py-16">
          <ErrorState message="No dashboard data was returned. Check the API or student id." onRetry={load} />
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell subtitle={studentName ? `Student · ${studentName}'s learning map` : 'Student · Learning map'}>
      <div className="axon-card-subtle p-4 sm:p-5 space-y-3">
        <div className="space-y-2">
          <p className="axon-label mb-0">Mathematics</p>
          <h1 className="axon-h2 text-lg sm:text-xl text-slate-800">Your learning map</h1>
          <p className="text-xs leading-relaxed text-slate-500">
            Switch between the full prerequisite tree and explore mode. Click to open the path and see what comes next.
            Shaded columns show level (left = fundamentals).
          </p>
        </div>
      </div>

      {hasLearningGraph ? (
        <div className="mt-4 space-y-4 axon-card-subtle p-4 sm:p-5 sm:space-y-5">
          <div className="min-h-[min(68dvh,1400px)] overflow-hidden rounded-lg border border-[#2c2418]/10 p-1 sm:p-2">
            <KnowledgeGraphNew
              dataOverride={graphData}
              masteryMap={masteryMapForGraph}
              mapOnly
              focusKeyNodes
              defaultExploration="path"
            />
          </div>
        </div>
      ) : (
        <div className="mt-4 axon-card-subtle p-6 text-center text-sm text-slate-500">
          No learning map data is available yet.
        </div>
      )}
    </DashboardShell>
  );
}

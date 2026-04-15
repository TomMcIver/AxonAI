import { useEffect, useMemo, useRef, useState } from 'react';
import { getClassConceptSummary, getClassOverview, getStudentMastery } from '../api/axonai';
import {
  aggregateClassMasteryFromIndividualMasteries,
  masteryMapFromClassSummary,
} from '../utils/classMasteryFair';
import { DEMO_STUDENT_IDS, filterDemoStudents } from '../constants/demoStudents';

const BATCH = 8;

function resolveStudentIds(overviewStudents, explicitIds) {
  if (Array.isArray(explicitIds) && explicitIds.length > 0) {
    return [...new Set(explicitIds.map((id) => Number(id)).filter((id) => DEMO_STUDENT_IDS.includes(id)))];
  }
  const fromOv = filterDemoStudents(overviewStudents).map((s) => s.student_id ?? s.id);
  return fromOv.length ? fromOv : [...DEMO_STUDENT_IDS];
}

/**
 * Class-wide concept → mastery map for teacher graphs.
 * 1) Prefer GET /class/{id}/concept-summary when it returns rows.
 * 2) Otherwise pull GET /student/{id}/mastery for each locally displayed learner,
 *    average per concept, then apply the same fair cohort transform.
 *
 * @param {object} [options]
 * @param {number[]} [options.studentIds] — if set (e.g. from class roster), only these learners; still restricted to demo IDs.
 */
export function useClassMasteryMap(classId, subject, options = {}) {
  const [masteryMap, setMasteryMap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState(null);
  const [studentCount, setStudentCount] = useState(0);

  const studentIdsKey = useMemo(() => {
    const arr = options?.studentIds;
    if (!Array.isArray(arr) || arr.length === 0) return '';
    return [...new Set(arr.map((x) => Number(x)))]
      .filter((id) => DEMO_STUDENT_IDS.includes(id))
      .sort((a, b) => a - b)
      .join(',');
  }, [options?.studentIds]);

  const studentIdsRef = useRef(options?.studentIds);
  studentIdsRef.current = options?.studentIds;

  useEffect(() => {
    let cancelled = false;

    async function run() {
      setLoading(true);
      setMasteryMap(null);
      setSource(null);
      setStudentCount(0);

      try {
        const summary = await getClassConceptSummary(classId).catch(() => null);
        if (cancelled) return;
        const fromApi = masteryMapFromClassSummary(summary);
        if (fromApi && Object.keys(fromApi).length > 0) {
          setMasteryMap(fromApi);
          setSource('class-summary');
          setLoading(false);
          return;
        }
      } catch {
        /* fall through */
      }

      let ids = [];
      try {
        const overview = await getClassOverview(classId).catch(() => null);
        if (cancelled) return;
        ids = resolveStudentIds(overview?.students, studentIdsRef.current);
      } catch {
        ids = resolveStudentIds(null, studentIdsRef.current);
      }
      if (ids.length === 0) {
        ids = [...DEMO_STUDENT_IDS];
      }

      const masteries = [];
      for (let i = 0; i < ids.length; i += BATCH) {
        if (cancelled) return;
        const chunk = ids.slice(i, i + BATCH);
        const part = await Promise.all(
          chunk.map((id) => getStudentMastery(id).catch(() => null)),
        );
        masteries.push(...part.filter(Boolean));
      }

      if (cancelled) return;

      const aggregated = aggregateClassMasteryFromIndividualMasteries(masteries, subject);
      setMasteryMap(aggregated);
      setSource(aggregated && Object.keys(aggregated).length > 0 ? 'student-aggregate' : null);
      setStudentCount(masteries.length);
      setLoading(false);
    }

    run();
    return () => {
      cancelled = true;
    };
  }, [classId, subject, studentIdsKey]);

  return { masteryMap, loading, source, studentCount };
}

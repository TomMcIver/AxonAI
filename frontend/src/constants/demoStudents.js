// The 26 demo students in class_id=1 that have full ML data seeded.
// This is the ONLY source of truth. Every component that filters, counts,
// or displays students must import from here. Never hardcode elsewhere.
// ML training excludes these ids (see ml/excluded_students.py FRONTEND_DEMO_STUDENT_IDS).

export const DEMO_STUDENT_IDS = [
  1, 547, 548, 549, 550, 551, 552, 553, 554, 555,
  556, 557, 558, 559, 560, 561, 562, 563, 564, 565,
  566, 567, 568, 569, 570, 571,
];

// Aroha Ngata (ID 1) is always pinned to the top of any student list.
export const AROHA_ID = 1;

// Sione Tuhoe (ID 559) is always surfaced first in Needs Attention.
export const SIONE_ID = 559;

/**
 * Filter an array of student objects to only demo students.
 * Handles both .student_id and .id field shapes.
 */
export function filterDemoStudents(students) {
  return (students || []).filter(
    s => DEMO_STUDENT_IDS.includes(s.student_id ?? s.id)
  );
}

/**
 * Sort students so Aroha is always first, then by the given comparator.
 * Pass a compareFn(a, b) for secondary sort (e.g. risk score desc).
 */
export function sortWithArohaFirst(students, compareFn = null) {
  return [...students].sort((a, b) => {
    const aId = a.student_id ?? a.id;
    const bId = b.student_id ?? b.id;
    if (aId === AROHA_ID) return -1;
    if (bId === AROHA_ID) return 1;
    return compareFn ? compareFn(a, b) : 0;
  });
}

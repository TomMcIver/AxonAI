#!/usr/bin/env python
"""
CLI script to generate demo school data.

Usage:
    python scripts/simulate_school.py --students 500 --days 30 --classes 6 --seed 42
"""

import os
import sys
import argparse
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description='Generate demo school data')
    parser.add_argument('--students', type=int, default=100, help='Number of students')
    parser.add_argument('--days', type=int, default=30, help='Days of data to generate')
    parser.add_argument('--classes', type=int, default=3, help='Number of classes')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--subject', type=str, default='math', help='Subject area')
    parser.add_argument('--teacher-id', type=int, default=None, help='Teacher user ID')
    parser.add_argument('--dry-run', action='store_true', help='Generate but do not save to DB')
    parser.add_argument('--output', type=str, default=None, help='Output JSON file for dry run')
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                   AxonAI Demo Data Simulator                      ║
╠══════════════════════════════════════════════════════════════════╣
║  Students: {args.students:>6}  │  Days: {args.days:>4}  │  Classes: {args.classes:>3}          ║
║  Subject: {args.subject:<10}  │  Seed: {args.seed:>6}                          ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    from simulator import CohortBuilder
    
    print("Generating cohort data...")
    builder = CohortBuilder(seed=args.seed)
    cohort = builder.build_cohort(
        n_students=args.students,
        n_classes=args.classes,
        n_days=args.days,
        subject=args.subject
    )
    
    print(f"\nGenerated:")
    print(f"  - {len(cohort['students'])} students")
    print(f"  - {len(cohort['classes'])} classes")
    print(f"  - {len(cohort['interactions'])} interactions")
    print(f"  - {len(cohort['quizzes'])} quizzes")
    print(f"  - {len(cohort['mastery_states'])} mastery states")
    
    if args.dry_run:
        if args.output:
            with open(args.output, 'w') as f:
                def serialize(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    if hasattr(obj, 'isoformat'):
                        return obj.isoformat()
                    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
                
                json.dump(cohort, f, default=serialize, indent=2)
            print(f"\nData saved to: {args.output}")
        else:
            print("\nDry run complete. Use --output to save data to file.")
        return
    
    print("\nPopulating database...")
    
    from app import app, db
    from models import User
    
    with app.app_context():
        teacher_id = args.teacher_id
        if teacher_id is None:
            teacher = User.query.filter_by(role='teacher').first()
            if teacher:
                teacher_id = teacher.id
            else:
                teacher = User(
                    first_name='Demo',
                    last_name='Teacher',
                    role='teacher',
                    is_active=True
                )
                db.session.add(teacher)
                db.session.commit()
                teacher_id = teacher.id
                print(f"Created demo teacher with ID: {teacher_id}")
        
        result = builder.populate_database(db, app, cohort, teacher_id)
        
        print(f"\nDatabase populated:")
        print(f"  - Classes created: {len(result['class_map'])}")
        print(f"  - Students created: {len(result['student_map'])}")
        print(f"  - Interactions created: {result['n_interactions']}")
        print(f"  - Mastery states created: {result['n_mastery_states']}")
    
    print("\n✓ Demo data generation complete!")
    print("\nNext steps:")
    print("  1. Run training: python training/train_mastery.py")
    print("  2. Run training: python training/train_risk.py")
    print("  3. Evaluate: python training/evaluate.py")


if __name__ == '__main__':
    main()

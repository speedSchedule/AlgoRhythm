import random

# 1. 기초 데이터 (홍길동 스타일)
TEACHERS = {
    "국어": "홍길동", "수학": "임꺽정", "영어": "김선달", "한국사": "심청",
    "사회": "전우치", "과학": "장길산", "체육": "이춘풍", "예술": "황진이",
    "정보": "허균", "과탐실": "박지원", "창체": "심봉사"
}

CLASSES = ["1-1", "1-2"]
# 요일별 교시 제한 설정 (월7, 화7, 수6, 목6, 금6)
DAYS_LIMIT = {"월": 7, "화": 7, "수": 6, "목": 6, "금": 6}

# 2. 32시간 시수 배정 (합계: 32)
CURRICULUM_UNITS = [
    ("국어", 4), ("수학", 4), ("영어", 4), ("사회", 4),
    ("과학", 4), ("한국사", 3), ("체육", 2), ("예술", 2),
    ("정보", 2), ("과탐실", 1)
    # 창체(2)는 고정 배정으로 별도 처리하여 총 32시간
]

# 창체 고정 슬롯 (금요일 5, 6교시)
FIXED_SLOTS = [("금", 5), ("금", 6)]

class HighSchoolSchedule:
    def __init__(self):
        self.timetable = []
        self.fitness = 0

    def initialize(self):
        """설정된 요일별 교시 제한 내에서 배정"""
        for class_name in CLASSES:
            # 창체 고정 배정
            for day, period in FIXED_SLOTS:
                self.timetable.append({
                    'class': class_name, 'subject': "창체", 'teacher': TEACHERS["창체"],
                    'day': day, 'period': period, 'is_fixed': True
                })

            # 나머지 30시간 교과 배정
            for subject, weekly_hours in CURRICULUM_UNITS:
                for _ in range(weekly_hours):
                    while True:
                        d = random.choice(list(DAYS_LIMIT.keys()))
                        p = random.randint(1, DAYS_LIMIT[d])

                        # 이미 배정된 칸인지, 고정 슬롯인지 확인
                        occupied = any(e['class'] == class_name and e['day'] == d and e['period'] == p for e in self.timetable)
                        if not occupied:
                            self.timetable.append({
                                'class': class_name, 'subject': subject, 'teacher': TEACHERS[subject],
                                'day': d, 'period': p, 'is_fixed': False
                            })
                            break

    def calculate_fitness(self):
        score = 1000
        teacher_busy = set()
        class_busy = set()
        subject_today = set()

        for entry in self.timetable:
            t_key = (entry['teacher'], entry['day'], entry['period'])
            c_key = (entry['class'], entry['day'], entry['period'])
            s_key = (entry['class'], entry['day'], entry['subject'])

            # Hard Constraints
            if t_key in teacher_busy: score -= 100
            teacher_busy.add(t_key)

            if c_key in class_busy: score -= 100
            class_busy.add(c_key)

            # 규칙 1: 하루 동일 과목 중복 금지 (창체 제외)
            if entry['subject'] != "창체":
                if s_key in subject_today:
                    score -= 50
                subject_today.add(s_key)

        self.fitness = score
        return score

def run_scheduling():
    population = [HighSchoolSchedule() for _ in range(30)]
    for s in population: s.initialize()

    for gen in range(500):
        population.sort(key=lambda x: x.calculate_fitness(), reverse=True)
        if population[0].fitness >= 1000: break

        next_gen = population[:10]
        while len(next_gen) < 30:
            parent = random.choice(population[:10])
            child = HighSchoolSchedule()
            child.timetable = [e.copy() for e in parent.timetable]

            # 변이: 고정되지 않은 수업 위치 변경
            m = random.choice([e for e in child.timetable if not e['is_fixed']])
            while True:
                new_d = random.choice(list(DAYS_LIMIT.keys()))
                new_p = random.randint(1, DAYS_LIMIT[new_d])
                if (new_d, new_p) not in FIXED_SLOTS:
                    # 해당 칸이 비어있는지 확인 (단순 교체 로직)
                    m['day'], m['period'] = new_d, new_p
                    break
            next_gen.append(child)
        population = next_gen

    # 결과 출력
    best = population[0]
    print(f"--- 32시간 배정 완료 (적합도: {best.fitness}) ---")

    teacher_hours = {}
    for entry in best.timetable:
        t_name = entry['teacher']
        # 학급별로 각각 집계 (1-1반 1시간 + 1-2반 1시간 = 총 2시간 수업)
        teacher_hours[t_name] = teacher_hours.get(t_name, 0) + 1

    print("\n" + "="*40)
    print(f"{'교사명':<8} | {'담당 과목':<8} | {'주간 총 시수'}")
    print("-" * 40)

    # 정렬하여 출력 (시수가 많은 순서대로)
    sorted_teachers = sorted(teacher_hours.items(), key=lambda x: x[1], reverse=True)
    for t_name, hours in sorted_teachers:
        # TEACHERS 딕셔너리에서 과목명 찾기
        subj = [k for k, v in TEACHERS.items() if v == t_name][0]
        print(f"{t_name:<10} | {subj:<10} | {hours:>2}시간")
    print("="*40)

    for day in DAYS_LIMIT.keys():
        print(f"\n[{day}요일 - {DAYS_LIMIT[day]}교시 체제]")
        for p in range(1, DAYS_LIMIT[day] + 1):
            row = []
            for c in CLASSES:
                found = [e for e in best.timetable if e['class'] == c and e['day'] == day and e['period'] == p]
                row.append(f"{c}: {found[0]['subject']}({found[0]['teacher']})" if found else f"{c}: [공강]")
            print(f"{p}교시 | {' | '.join(row)}")

if __name__ == "__main__":
    run_scheduling()

import sys
from typing import List, Dict, Optional

class Competition:
    def __init__(self):
        self._challenges: List[Challenge] = []
        self._students: List[Student] = []

    def read_results(self, filename: str):
        try:
            with open(filename, 'r') as file:
                challenge_ids = file.readline().strip().split(', ')[1:]
                for challenge_id in challenge_ids:
                    Challenge.get_challenge(challenge_id)

                for line in file:
                    parts = line.strip().split()
                    student_id = parts[0]
                    student = Student.get_student(student_id)

                    for i, time_str in enumerate(parts[1:]):
                        time = float(time_str.strip(","))
                        student.add_result(challenge_ids[i], time)

                self._challenges = Challenge.get_all_challenges()
                self._students = Student.get_all_students()
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            sys.exit(1)

    def get_nfinish_and_nongoing_for_challenge(self, challenge_id: str) -> tuple:
        nfinish = 0
        nongoing = 0

        for student in self._students:
            result = student.get_result(challenge_id)
            if result != 444 and result != -1:
                nfinish += 1
            elif result == 444:
                nongoing += 1

        return nfinish, nongoing

    def get_finish_times_for_challenge(self, challenge_id: str) -> list:
        finish_times = []
        for student in Student._all_students.values():
            if student.is_completed(challenge_id):
                finish_times.append(student._finish_times[challenge_id])
        return finish_times

    def display_results(self):
        if not self._challenges or not self._students:
            print("[Usage:] python my_competition.py <result file>")
            return

        print("COMPETITION DASHBOARD")
        headers = ["Results"] + [challenge.id.replace(",", "") for challenge in self._challenges]
        col_widths = [max(len(str(h)), 6) for h in headers]
        line_separator = "-" * (sum(col_widths) + len(col_widths) * 3 + 1)

        print(line_separator)
        header_row = "| " + " | ".join(f"{header:<{col_widths[i]}}" for i, header in enumerate(headers)) + " |"
        print(header_row)
        print(line_separator)

        for student in self._students:
            row = [student.id]
            for challenge in self._challenges:
                result = student.get_result(challenge.id)
                if result == -1:
                    row.append("")
                elif result == 444:
                    row.append("--")
                else:
                    row.append(f"{result:.1f}")

            row = [str(cell).replace(",", "") for cell in row]
            data_row = "| " + " | ".join(f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row)) + " |"
            print(data_row)
        print(line_separator)
        print(f"There are {len(self._students)} students and {len(self._challenges)} challenges")

        fastest_student = min(self._students,
                              key=lambda s: s.get_average_completion_time())
        avg_time = fastest_student.get_average_completion_time()
        if avg_time != float('inf'):
            print(f"The top student is {fastest_student.id} with an average time of {avg_time:.2f} minutes.")

class Challenge:
    _all_challenges: Dict[str, 'Challenge'] = {}

    def __init__(self, challenge_id: str, name: str = "", challenge_type: str = "M", weight: float = 1.0):
        self._id = challenge_id
        self._name = name
        self._type = challenge_type.upper()
        self._weight = weight
        self._results = []

        Challenge._all_challenges[challenge_id] = self

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, value: str):
        self._type = value.upper()
        if self._type == "M":
            self._weight = 1.0

    @property
    def weight(self) -> float:
        return self._weight

    @weight.setter
    def weight(self, value: float):
        if self._type == "S" and value <= 1.0:
            raise ValueError("Weight must be greater than 1.0")
        self._weight = value

    def add_result(self, time: float):
        self._results.append(time)
    @classmethod
    def get_challenge(cls, challenge_id: str) -> 'Challenge':
        if challenge_id not in cls._all_challenges:
            cls._all_challenges[challenge_id] = Challenge(challenge_id)
        return cls._all_challenges[challenge_id]

    @classmethod
    def get_all_challenges(cls) -> List['Challenge']:
        return list(cls._all_challenges.values())

    @classmethod
    def load_challenges_from_file(cls, filename: str):
        cls._all_challenges.clear()
        try:
            with open(filename, 'r') as file:
                for line_number, line in enumerate(file, 1):
                    if not line.strip() or line.strip().startswith('#'):
                        continue
                    try:
                        parts = [part.strip() for part in line.strip().split(', ')]
                        if len(parts) < 4:
                            print(f"Error on line {line_number}: Expected 4 values, got {len(parts)}")
                            continue

                        challenge_id = parts[0]
                        challenge_type = parts[1]
                        name = parts[2]
                        weight = float(parts[3])

                        if challenge_id not in cls._all_challenges:
                            new_challenge = cls(challenge_id, name, challenge_type, weight)
                            cls._all_challenges[challenge_id] = new_challenge

                    except ValueError as e:
                        print(f"Error parsing line {line_number}: {line.strip()}")
                        print(f"Error details: {str(e)}")
                        continue
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            sys.exit(1)
    def get_statistics(self, competition:Competition) -> Dict[str, float]:
        challenge_id = self._id
        nfinish, nongoing = competition.get_nfinish_and_nongoing_for_challenge(challenge_id)
        finish_times = competition.get_finish_times_for_challenge(challenge_id)

        average_time = 0.0
        if nfinish > 0:
            average_time = sum(finish_times) / nfinish

        return {
            "Nfinish": nfinish,
            "Nongoing": nongoing,
            "AverageTime": round(average_time,2)
        }

    @classmethod
    def display_challenge_statistics(cls, competition):
        if not cls._all_challenges:
            print("No challenges found.")
            return

        headers = ["Challenge", "Name", "Weight", "Nfinish", "Nongoing", "AverageTime"]
        challenges = sorted(cls._all_challenges.values(), key=lambda x: x.id)

        col_widths = [max(len(header), max(len(str(getattr(c, attr.lower(), ""))) for c in challenges)) for header, attr
                      in zip(headers, headers)]

        col_widths[1] = max(len(headers[1]), max(len(f"{c.name}({c.type})") for c in challenges))

        line_separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        print("\nCHALLENGE INFORMATION")
        print(line_separator)
        header_row = "| " + " | ".join(f"{header:<{col_widths[i]}}" for i, header in enumerate(headers)) + " |"
        print(header_row)
        print(line_separator)

        max_avg_time = 0
        max_avg_challenge_id = None
        max_avg_challenge_name = None

        for challenge in challenges:
            stats = challenge.get_statistics(competition)
            avg_time = stats['AverageTime']
            if avg_time > max_avg_time:
                max_avg_time = avg_time
                max_avg_challenge_id = challenge.id
                max_avg_challenge_name = challenge.name
            row = [
                challenge.id,
                f"{challenge.name}({challenge.type})",
                f"{challenge.weight:.1f}",
                str(stats["Nfinish"]),
                str(stats["Nongoing"]),
                f"{stats['AverageTime']:.2f}" if stats['AverageTime'] > 0 else "--"
            ]
            data_row = "| " + " | ".join(f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row)) + " |"
            print(data_row)
        print(line_separator)

        if max_avg_challenge_id:
            print(f"The most difficult challenge is {max_avg_challenge_name} ({max_avg_challenge_id}) with an average time of {max_avg_time:.2f} minutes")
        cls.save_competition_report(challenges, competition)
    @classmethod
    def save_competition_report(cls, challenges, competition, file_name='competition_report.txt'):
        with open(file_name, 'w') as file:
            file.write("ID, Name, Weight, Nfinish, Nongoing, AverageTime\n")

            for challenge in challenges:
                stats = challenge.get_statistics(competition)
                avg_time = stats['AverageTime']

                row = [
                    challenge.id,
                    f"{challenge.name}({challenge.type})",
                    f"{challenge.weight:.1f}",
                    str(stats["Nfinish"]),
                    str(stats["Nongoing"]),
                    f"{avg_time:.2f}" if avg_time > 0 else "--"
                ]
                file.write(", ".join(row) + "\n")
        print(f"Report {file_name} generated ")

class Student:
    _all_students: Dict[str, 'Student'] = {}

    def __init__(self, student_id: str):
        self._id = student_id
        # self.name = name
        # self.student_type = student_type
        self._results: Dict[str, float] = {}
        self._finish_times: Dict[str, float] = {}
        Student._all_students[student_id] = self

    @property
    def id(self) -> str:
        return self._id

    def set_finish_time(self, challenge_id: str, finish_time: float):
        self._finish_times[challenge_id] = finish_time

    def is_completed(self, challenge_id: str) -> bool:
        result = self._results.get(challenge_id, -1)
        return result != -1 and result != 444

    def add_result(self, challenge_id: str, time: float):
        self._results[challenge_id] = time
        if time != 444:
            self._finish_times[challenge_id] = time

    def get_result(self, challenge_id: str) -> Optional[float]:
        return self._results.get(challenge_id)

    def get_average_completion_time(self) -> float:
        completed_times = [time for time in self._results.values()
                           if time > 0 and time != 444]

        if completed_times:
            total_time = sum(completed_times)
            count = len(completed_times)
            avg_time = total_time / count
            return round(avg_time, 4)
        else:
            return float('inf')
    @classmethod
    def get_student(cls, student_id: str) -> 'Student':
        if student_id not in cls._all_students:
            cls._all_students[student_id] = Student(student_id)
        return cls._all_students[student_id]

    @classmethod
    def get_all_students(cls) -> List['Student']:
        return list(cls._all_students.values())


def main():
    if len(sys.argv) == 1:
        print("[Usage:] python my_competition.py <result file> <challenges file>")
        return
    elif len(sys.argv) == 2:
        results_file = sys.argv[1]
        challenges_file = None
    elif len(sys.argv) == 3:
        results_file = sys.argv[1]
        challenges_file = sys.argv[2]
    else:
        print("[Usage:] python my_competition.py <result file> <challenges file>")
        return

    competition = Competition()
    competition.read_results(results_file)
    competition.display_results()

    if challenges_file:
        Challenge.load_challenges_from_file(challenges_file)
        Challenge.display_challenge_statistics(competition)

if __name__ == "__main__":
    main()
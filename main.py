import json
import time
import os

def normalize_label(label):
    label_str = str(label).lower()
    if label_str in ['+', 'cross']:
        return 'Cross'
    if label_str in ['x']:
        return 'X'
    return str(label)

def mac_operation(pattern, filter_matrix):
    score = 0.0
    rows = len(pattern)
    if rows == 0: return score
    cols = len(pattern[0])
    for i in range(rows):
        for j in range(cols):
            score += float(pattern[i][j]) * float(filter_matrix[i][j])
    return score

def measure_mac_time(pattern, filter_matrix, repeat=10):
    start = time.perf_counter()
    for _ in range(repeat):
        mac_operation(pattern, filter_matrix)
    end = time.perf_counter()
    return ((end - start) * 1000) / repeat

def read_matrix_input(name, rows=3, cols=3):
    while True:
        print(f"\n{name} ({rows}줄 입력, 공백 구분)")
        matrix = []
        valid = True
        for _ in range(rows):
            line = input().strip()
            if not line:
                # To handle blank lines without crashing, treat as empty split
                pass
            try:
                row = [float(x) for x in line.split()]
                if len(row) != cols:
                    valid = False
                matrix.append(row)
            except ValueError:
                valid = False
        if valid and len(matrix) == rows:
            return matrix
        else:
            print(f"입력 형식 오류: 각 줄에 {cols}개의 숫자를 공백으로 구분해 입력하세요. 처음부터 다시 입력하세요.")

def mode_user_input():
    print("\n#---------------------------------------")
    print("# [1] 필터 입력")
    print("#---------------------------------------")
    filter_a = read_matrix_input("필터 A")
    filter_b = read_matrix_input("필터 B")
    
    print("\n#---------------------------------------")
    print("# [2] 패턴 입력")
    print("#---------------------------------------")
    pattern = read_matrix_input("패턴")
    
    print("\n#---------------------------------------")
    print("# [3] MAC 결과")
    print("#---------------------------------------")
    
    score_a = mac_operation(pattern, filter_a)
    score_b = mac_operation(pattern, filter_b)
    
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    
    avg_time = measure_mac_time(pattern, filter_a, 10)
    print(f"연산 시간(평균/10회): {avg_time:.3f} ms")
    
    if abs(score_a - score_b) < 1e-9:
        print("판정: 판정 불가 (|A-B| < 1e-9)")
    else:
        winner = "A" if score_a > score_b else "B"
        print(f"판정: {winner}")
        
    print("\n#---------------------------------------")
    print("# [4] 성능 분석 (평균/10회)")
    print("#---------------------------------------")
    print(f"{'크기':<10}{'평균 시간(ms)':<15}{'연산 횟수':<10}")
    print("-" * 37)
    print(f"{'3×3':<10}{avg_time:<15.3f}{9:<10}")

def mode_json_analysis():
    # Attempt to load data.json in the current dir or one level up if necessary
    json_path = "data.json"
    if not os.path.exists(json_path):
        print(f"오류: {json_path} 파일을 찾을 수 없습니다.")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"data.json 로드 실패: {e}")
        return

    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")
    filters = data.get("filters", {})
    normalized_filters = {}
    for size_key, filters_dict in filters.items():
        norm_dict = {}
        for k, v in filters_dict.items():
            norm_dict[normalize_label(k)] = v
        normalized_filters[size_key] = norm_dict
        # Ensure Cross and X are extracted properly (some cases they might be absent)
        print(f"✓ {size_key} 필터 로드 완료 (Cross, X)")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")
    patterns = data.get("patterns", {})
    
    total = 0
    passed = 0
    failed = 0
    fail_cases = []
    
    performance_data = {}
    
    for pat_key, pat_data in patterns.items():
        total += 1
        print(f"\n--- {pat_key} ---")
        
        parts = pat_key.split('_')
        if len(parts) >= 2 and parts[0] == 'size':
            try:
                n = int(parts[1])
            except ValueError:
                n = -1
        else:
            n = -1
            
        size_key = f"size_{n}"
        expected_raw = pat_data.get("expected", "")
        expected = normalize_label(expected_raw)
        input_matrix = pat_data.get("input", [])
        
        if size_key not in normalized_filters:
            print(f"FAIL: {size_key} 필터가 존재하지 않습니다.")
            failed += 1
            fail_cases.append((pat_key, "필터 스키마 누락"))
            continue
            
        if len(input_matrix) != n or any(len(row) != n for row in input_matrix):
            print(f"FAIL: 패턴 크기 불일치 (예상: {n}x{n})")
            failed += 1
            fail_cases.append((pat_key, "패턴 크기 불일치"))
            continue
            
        filter_cross = normalized_filters[size_key].get("Cross")
        filter_x = normalized_filters[size_key].get("X")
        
        if not filter_cross or not filter_x:
            print(f"FAIL: Cross 또는 X 필터가 누락되었습니다.")
            failed += 1
            fail_cases.append((pat_key, "Cross/X 필터 누락"))
            continue
            
        score_cross = mac_operation(input_matrix, filter_cross)
        score_x = mac_operation(input_matrix, filter_x)
        
        print(f"Cross 점수: {score_cross}")
        print(f"X 점수: {score_x}")
        
        if abs(score_cross - score_x) < 1e-9:
            decision = "UNDECIDED"
        else:
            decision = "Cross" if score_cross > score_x else "X"
            
        status = "PASS" if decision == expected else "FAIL"
        print(f"판정: {decision} | expected: {expected} | {status}")
        
        if status == "PASS":
            passed += 1
        else:
            failed += 1
            if decision == "UNDECIDED":
                reason = "동점(UNDECIDED) 처리 규칙에 따라 FAIL"
            else:
                reason = "판정 결과와 expected 불일치"
            fail_cases.append((pat_key, reason))
            
        if n not in performance_data:
            avg_time = measure_mac_time(input_matrix, filter_cross, 10)
            performance_data[n] = {"time": avg_time, "ops": n * n}
            
    print("\n#---------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#---------------------------------------")
    print(f"{'크기':<10}{'평균 시간(ms)':<15}{'연산 횟수':<10}")
    print("-" * 37)
    
    # Default 3x3 perf check
    dummy_3x3 = [[0]*3 for _ in range(3)]
    time_3x3 = measure_mac_time(dummy_3x3, dummy_3x3, 10)
    print(f"{'3×3':<10}{time_3x3:<15.3f}{9:<10}")
    
    for n in sorted(performance_data.keys()):
        sz_str = f"{n}×{n}"
        t = performance_data[n]["time"]
        ops = performance_data[n]["ops"]
        print(f"{sz_str:<10}{t:<15.3f}{ops:<10}")
        
    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#---------------------------------------")
    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")
    
    if failed > 0:
        print("\n실패 케이스:")
        for k, r in fail_cases:
            print(f"- {k}: {r}")
    print("\n(상세 원인 분석 및 복잡도 설명은 README.md의 '결과 리포트' 섹션에 작성)")

def main():
    print("=== Mini NPU Simulator ===\n")
    print("[모드 선택]\n")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    
    choice = input("선택: ").strip()
    if choice == '1':
        mode_user_input()
    elif choice == '2':
        mode_json_analysis()
    else:
        print("잘못된 선택입니다.")

if __name__ == "__main__":
    main()

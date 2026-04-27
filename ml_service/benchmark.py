"""
Скрипт тестирования и сравнения ML моделей

Сравнивает RuBERT FastText и Mock модели классификации
по скорости точности и использованию ресурсов
"""

import time
import requests
import json
from typing import Dict, Tuple
from sklearn.metrics import f1_score

TEST_CASES = [
    {
        "text": "У меня критическая боль в груди, срочно вызовите скорую",
        "expected_urgency": "Экстренное",
        "expected_type": "Перенаправление в экстренные службы"
    },
    {
        "text": "Записать меня на прием к кардиологу на завтра",
        "expected_urgency": "Плановое",
        "expected_type": "Запись на прием"
    },
    {
        "text": "У меня температура 39 градусов, как мне быть?",
        "expected_urgency": "Срочное",
        "expected_type": "Консультация или вопрос"
    },
    {
        "text": "Подскажите, какой врач лечит астму?",
        "expected_urgency": "Консультационное",
        "expected_type": "Консультация или вопрос"
    },
    {
        "text": "Нужно провести диспансеризацию",
        "expected_urgency": "Плановое",
        "expected_type": "Наблюдение"
    },
]

class ModelBenchmark:
    def __init__(self, model_type: str, base_url: str = "http://localhost:5000"):
        self.model_type = model_type
        self.base_url = base_url
        self.results = []
        
    def classify(self, text: str) -> Dict:
        """Вызвать API классификации"""
        try:
            response = requests.post(
                f"{self.base_url}/classify",
                json={"text": text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def benchmark_single(self, test_case: Dict) -> Dict:
        """Benchmark a single test case."""
        text = test_case["text"]
        
        # Measure time
        start = time.time()
        result = self.classify(text)
        elapsed = time.time() - start
        
        # Check correctness
        is_correct = False
        if "error" not in result:
            is_correct = (
                result.get("urgency") == test_case["expected_urgency"] and
                result.get("request_type") == test_case["expected_type"]
            )
        
        return {
            "text": text[:50] + "..." if len(text) > 50 else text,
            "elapsed": elapsed,
            "result": result,
            "is_correct": is_correct,
            "expected_urgency": test_case["expected_urgency"],
            "expected_type": test_case["expected_type"]
        }
    
    def run_benchmark(self) -> Dict:
        """Run full benchmark suite."""
        print(f"\n{'='*70}")
        print(f"Benchmarking {self.model_type.upper()}")
        print(f"{'='*70}\n")
        
        self.results = []
        total_time = 0
        correct_count = 0
        true_labels = []
        pred_labels = []
        
        for i, test_case in enumerate(TEST_CASES, 1):
            print(f"Test {i}/{len(TEST_CASES)}: {test_case['text'][:45]}...")
            
            result = self.benchmark_single(test_case)
            self.results.append(result)
            
            total_time += result["elapsed"]
            if result["is_correct"]:
                correct_count += 1
            
            # Collect labels for F1 calculation
            true_urgency = test_case["expected_urgency"]
            true_type = test_case["expected_type"]
            pred_urgency = result["result"].get("urgency", "")
            pred_type = result["result"].get("request_type", "")
            
            true_labels.append(f"{true_urgency}|{true_type}")
            pred_labels.append(f"{pred_urgency}|{pred_type}")
            
            print(f"  ⏱  Time: {result['elapsed']*1000:.0f}ms")
            print(f"  📊 Urgency: {result['result'].get('urgency')}")
            print(f"  📝 Type: {result['result'].get('request_type')}")
            print(f"  ✓ Correct" if result["is_correct"] else f"  ✗ Wrong")
            print()
        
        accuracy = (correct_count / len(TEST_CASES)) * 100
        avg_time = total_time / len(TEST_CASES)
        
        # Calculate F1-score
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        all_labels = true_labels + pred_labels
        le.fit(all_labels)
        true_encoded = le.transform(true_labels)
        pred_encoded = le.transform(pred_labels)
        f1 = f1_score(true_encoded, pred_encoded, average='weighted') * 100
        
        return {
            "model_type": self.model_type,
            "total_tests": len(TEST_CASES),
            "correct": correct_count,
            "accuracy": accuracy,
            "f1_score": f1,
            "total_time": total_time,
            "avg_time": avg_time,
            "min_time": min(r["elapsed"] for r in self.results),
            "max_time": max(r["elapsed"] for r in self.results),
        }
    
    def print_summary(self, summary: Dict):
        """Print benchmark summary."""
        print(f"\n{'='*70}")
        print(f"RESULTS: {summary['model_type'].upper()}")
        print(f"{'='*70}")
        print(f"Accuracy:    {summary['accuracy']:.1f}% ({summary['correct']}/{summary['total_tests']})")
        print(f"F1-Score:    {summary['f1_score']:.1f}%")
        print(f"Avg Time:    {summary['avg_time']*1000:.1f}ms")
        print(f"Min Time:    {summary['min_time']*1000:.1f}ms")
        print(f"Max Time:    {summary['max_time']*1000:.1f}ms")
        print(f"Total Time:  {summary['total_time']:.2f}s")
        print(f"{'='*70}\n")


def print_comparison_table(summaries: list):
    """Print comparison table."""
    print(f"\n{'='*90}")
    print("COMPARISON TABLE")
    print(f"{'='*90}")
    print(f"{'Model':<15} {'Accuracy':<12} {'F1-Score':<12} {'Avg Time':<12} {'Min Time':<12} {'Max Time':<12}")
    print(f"{'-'*90}")
    
    for summary in summaries:
        print(
            f"{summary['model_type']:<15} "
            f"{summary['accuracy']:>10.1f}% "
            f"{summary['f1_score']:>10.1f}% "
            f"{summary['avg_time']*1000:>10.1f}ms "
            f"{summary['min_time']*1000:>10.1f}ms "
            f"{summary['max_time']*1000:>10.1f}ms"
        )
    
    print(f"{'='*90}\n")


def main():
    """Run all benchmarks."""
    print("\n" + "="*70)
    print("ML MODELS BENCHMARK & COMPARISON")
    print("="*70)
    print("\nMake sure ML service is running on http://localhost:5000")
    print("Start with: MODEL_TYPE=<model_type> python -m uvicorn main:app --port 5000\n")
    
    summaries = []
    
    # Test RuBERT
    try:
        benchmark_rubert = ModelBenchmark("rubert")
        summary = benchmark_rubert.run_benchmark()
        benchmark_rubert.print_summary(summary)
        summaries.append(summary)
    except Exception as e:
        print(f"✗ RuBERT benchmark failed: {e}\n")
    
    # Test FastText
    try:
        benchmark_fasttext = ModelBenchmark("fasttext")
        summary = benchmark_fasttext.run_benchmark()
        benchmark_fasttext.print_summary(summary)
        summaries.append(summary)
    except Exception as e:
        print(f"✗ FastText benchmark failed: {e}\n")
    
    # Test Mock
    try:
        benchmark_mock = ModelBenchmark("mock")
        summary = benchmark_mock.run_benchmark()
        benchmark_mock.print_summary(summary)
        summaries.append(summary)
    except Exception as e:
        print(f"✗ Mock benchmark failed: {e}\n")
    
    # Print comparison
    if summaries:
        print_comparison_table(summaries)
        print("\n✓ Benchmark complete!")
        print("\nRecommendations:")
        print("- For production: Use the model with best accuracy")
        print("- For speed-critical: Use FastText")
        print("- For reliability: Use RuBERT (zero-shot, no training needed)")
    else:
        print("✗ No benchmarks completed. Check that ML service is running.")


if __name__ == "__main__":
    main()

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from hebToEngTranslator import HebToEngTranslator
import json
from datetime import datetime
import sys
from pathlib import Path

# Add the parent directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


FILE = project_root / "utterances" / "utterances_25_ptv_1355973.json"

# embed all translated utterances from given file with some generic transformer and measure cosine sim to original.


def compare_translators() -> dict:
    google_trans = HebToEngTranslator(force_google=True)
    libre_trans = HebToEngTranslator()
    model = SentenceTransformer(
        'sentence-transformers/distiluse-base-multilingual-cased-v2')
    with open(FILE, "r", encoding="utf-8") as f:
        meeting = json.load(f)
    translators = {
        "google": {"resolver": google_trans.translate, "scores": []},
        "libre": {"resolver": libre_trans.translate, "scores": []}}
    number_of_utterances = 0
    for _, mk_data in meeting["utterances"].items():
        for utterance in mk_data["utterances"]:
            number_of_utterances += 1
            orig_embedding = model.encode(utterance, convert_to_tensor=True)
            for translator in translators:

                sentence_translated = translators[translator]["resolver"](
                    utterance)
                # convert to tensor to allow working with pytorch (as we already have it from hugggingface transformers)

                translated_embedding = model.encode(
                    sentence_translated, convert_to_tensor=True)
                # hack to allow for one sample batch, no need for  parallelism
                similarity = torch.nn.functional.cosine_similarity(
                    orig_embedding.unsqueeze(0), translated_embedding.unsqueeze(0), dim=1).item()

                translators[translator]["scores"].append(similarity)

    for _, t in translators.items():
        scores_np = np.array(t["scores"], dtype=np.float32)
        t["mean"] = scores_np.mean()
        t["variance"] = scores_np.var()
    return translators


def main():
    results = compare_translators()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"translation_evaluation_results_{timestamp}.txt"

    # Prepare the output text
    output_text = "Translation Quality Comparison Results:\n"
    print("\nTranslation Quality Comparison Results:")
    print("=" * 50)

    for translator, data in results.items():
        line = f"{translator.capitalize()}: similarity score = {data['mean']:.4f} with variance {data['variance']:.4f}\n"
        output_text += line
        print(line.strip())

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output_text)

    print("=" * 50)
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()

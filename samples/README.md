# Samples

테스트 샘플을 여기에 둔다.

권장 구조:

```text
samples/
  videos/
    sample_01.mp4
    sample_02.mp4
  references/
    reference_01.jpg
  qa-template.md
```

주의:
- 샘플 영상과 참조 사진은 개인정보가 포함될 수 있으므로 저장소에 커밋하지 않는 것을 기본으로 한다.
- 원본 영상 대신 짧게 자른 테스트 클립을 사용한다.

현재 샘플:
- `samples/videos/akiyo_cif.y4m`: Xiph.org Derf test media `akiyo` CIF 원본.
- `samples/videos/akiyo_short.mp4`: 파이프라인 반복 테스트용 짧은 클립.
- `samples/references/akiyo_reference.jpg`: YOLO가 잡은 얼굴 crop 기반 참조 이미지.

반복 실행:

```bash
python tools/prepare_sample.py --max-frames 90
python tools/run_sample_pipeline.py --mode preserve --output samples/outputs/akiyo_preserve.mp4 --report samples/reports/akiyo_preserve.json
python tools/run_sample_pipeline.py --mode character --output samples/outputs/akiyo_character.mp4 --report samples/reports/akiyo_character.json
python tools/export_sample_contact_sheet.py
```

/**
 * i18n - 한국어/영어 번역 모듈
 */

type Translations = Record<string, Record<string, string>>;

const translations: Translations = {
  ko: {
    activated: "VIBE-X Extension 활성화 완료",
    no_file_open: "열려있는 파일이 없습니다",
    checking_file: "파일 검사 중...",
    scanning: "${count}개 파일 스캔 중...",
    scan_complete: "스캔 완료: ${files}개 파일, ${issues}개 이슈 발견",
    all_passed: "전체 통과",
    enter_username: "팀원 이름을 입력하세요",
    zone_declared: "Work Zone 선언 완료: ${file} (${user})",
    last_updated: "마지막 업데이트",
  },
  en: {
    activated: "VIBE-X Extension activated",
    no_file_open: "No file is open",
    checking_file: "Checking file...",
    scanning: "Scanning ${count} files...",
    scan_complete: "Scan complete: ${files} files, ${issues} issues found",
    all_passed: "All Passed",
    enter_username: "Enter your team member name",
    zone_declared: "Work Zone declared: ${file} (${user})",
    last_updated: "Last updated",
  },
};

export class I18n {
  private lang: string;

  constructor(lang: string = "ko") {
    this.lang = lang in translations ? lang : "ko";
  }

  t(key: string, params?: Record<string, string | number>): string {
    const dict = translations[this.lang] || translations["ko"];
    let text = dict[key] || key;

    if (params) {
      for (const [k, v] of Object.entries(params)) {
        text = text.replace(`\${${k}}`, String(v));
      }
    }

    return text;
  }

  setLanguage(lang: string): void {
    this.lang = lang in translations ? lang : "ko";
  }
}

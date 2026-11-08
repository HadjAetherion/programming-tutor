// 多语言编辑器支持：语言标识 → Monaco 语言 ID / 显示名 / 初始模板。
// 语言标识与后端 sandbox.SpecFor 保持一致：go / python / java / cpp。

export interface LanguageOption {
  value: string
  label: string
  monacoId: string
  template: string
}

export const LANGUAGES: LanguageOption[] = [
  {
    value: 'go',
    label: 'Go',
    monacoId: 'go',
    template: `package main

import (
    "fmt"
)

func main() {
    // Write your code here

    fmt.Println("Hello, World!")
}
`,
  },
  {
    value: 'python',
    label: 'Python',
    monacoId: 'python',
    template: `# Write your code here


print("Hello, World!")
`,
  },
  {
    value: 'java',
    label: 'Java',
    monacoId: 'java',
    template: `import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        // Write your code here

        System.out.println("Hello, World!");
    }
}
`,
  },
  {
    value: 'cpp',
    label: 'C++',
    monacoId: 'cpp',
    template: `#include <iostream>
using namespace std;

int main() {
    // Write your code here

    cout << "Hello, World!" << endl;
    return 0;
}
`,
  },
]

export function findLanguage(value: string): LanguageOption {
  return LANGUAGES.find((l) => l.value === value) ?? LANGUAGES[0]
}

export const LANGUAGE_LABELS: Record<string, string> = Object.fromEntries(
  LANGUAGES.map((l) => [l.value, l.label]),
)

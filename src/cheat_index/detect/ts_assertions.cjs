#!/usr/bin/env node
// Extracts test cases, skip markers and assertions from TypeScript/JavaScript test files
// with the TypeScript compiler API. Input on stdin: {"files": {"path": "source", ...}}.
// Output on stdout: {"typescript": "<version>", "files": {"path": {tests, assertions, parse_errors}}}.
"use strict";

const ts = require("typescript");

const TEST_FNS = new Set(["test", "it", "describe", "suite", "xit", "xtest", "xdescribe", "fit", "fdescribe"]);
const MODIFIERS = new Set(["skip", "todo", "only", "skipIf", "runIf", "fails", "concurrent", "each"]);
const LITERAL_KINDS = new Set([
  ts.SyntaxKind.StringLiteral,
  ts.SyntaxKind.NumericLiteral,
  ts.SyntaxKind.NoSubstitutionTemplateLiteral,
  ts.SyntaxKind.TrueKeyword,
  ts.SyntaxKind.FalseKeyword,
  ts.SyntaxKind.NullKeyword,
  ts.SyntaxKind.RegularExpressionLiteral,
  ts.SyntaxKind.BigIntLiteral,
]);

function isLiteral(node) {
  if (LITERAL_KINDS.has(node.kind)) return true;
  if (ts.isPrefixUnaryExpression(node) && ts.isNumericLiteral(node.operand)) return true;
  if (ts.isArrayLiteralExpression(node)) return node.elements.every(isLiteral);
  if (ts.isObjectLiteralExpression(node)) {
    return node.properties.every((p) => ts.isPropertyAssignment(p) && isLiteral(p.initializer));
  }
  if (ts.isIdentifier(node) && node.text === "undefined") return true;
  return false;
}

function calleeChain(expr) {
  // Returns ["expect", "not", "toBe"] style chains; call arguments in the middle are dropped.
  const parts = [];
  let cur = expr;
  while (cur) {
    if (ts.isPropertyAccessExpression(cur)) {
      parts.unshift(cur.name.text);
      cur = cur.expression;
    } else if (ts.isCallExpression(cur)) {
      cur = cur.expression;
    } else if (ts.isIdentifier(cur)) {
      parts.unshift(cur.text);
      cur = null;
    } else if (ts.isElementAccessExpression(cur)) {
      cur = cur.expression;
    } else {
      parts.unshift("?");
      cur = null;
    }
  }
  return parts;
}

function expectSubject(call) {
  // For expect(x).toBe(y): the arguments of the innermost expect(...) call.
  let cur = call.expression;
  while (cur) {
    if (ts.isCallExpression(cur) && ts.isIdentifier(cur.expression) && cur.expression.text === "expect") return cur;
    if (ts.isPropertyAccessExpression(cur) || ts.isCallExpression(cur)) cur = cur.expression;
    else return null;
  }
  return null;
}

function analyse(path, text) {
  const kind = /\.(tsx|jsx)$/.test(path) ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  const sf = ts.createSourceFile(path, text, ts.ScriptTarget.Latest, true, kind);
  const tests = [];
  const assertions = [];
  const lineOf = (n) => sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1;
  const stack = [];
  let tryDepth = 0;

  function visit(node) {
    let pushed = false;
    if (ts.isTryStatement(node)) {
      tryDepth += 1;
      visit(node.tryBlock);
      tryDepth -= 1;
      if (node.catchClause) visit(node.catchClause);
      if (node.finallyBlock) visit(node.finallyBlock);
      return;
    }
    if (ts.isCallExpression(node)) {
      const chain = calleeChain(node.expression);
      const head = chain[0];
      if (TEST_FNS.has(head) && chain.slice(1).every((m) => MODIFIERS.has(m))) {
        const first = node.arguments[0];
        const name = first && (ts.isStringLiteral(first) || ts.isNoSubstitutionTemplateLiteral(first)) ? first.text : null;
        let modifier = chain.find((m) => m === "skip" || m === "todo" || m === "only" || m === "skipIf") || null;
        if (head === "xit" || head === "xtest" || head === "xdescribe") modifier = "skip";
        let optionSkip = null;
        for (const arg of node.arguments.slice(1)) {
          if (ts.isObjectLiteralExpression(arg)) {
            for (const p of arg.properties) {
              if (ts.isPropertyAssignment(p) && ts.isIdentifier(p.name) && ["skip", "todo", "only"].includes(p.name.text)) {
                if (p.initializer.kind !== ts.SyntaxKind.FalseKeyword) optionSkip = p.name.text;
              }
            }
          }
        }
        const hasBody = node.arguments.some((a) => ts.isArrowFunction(a) || ts.isFunctionExpression(a));
        const kindName = head === "describe" || head === "suite" || head === "xdescribe" || head === "fdescribe" ? "suite" : "test";
        const full = [...stack, name ?? "?"].join(" > ");
        tests.push({ kind: kindName, name: full, modifier: modifier || optionSkip, has_body: hasBody, line: lineOf(node) });
        stack.push(name ?? "?");
        pushed = true;
      } else if (chain.length >= 2 && ["skip", "todo"].includes(chain[chain.length - 1]) && stack.length > 0 && head !== "assert") {
        // t.skip() / t.todo() inside a test body
        tests.push({ kind: "runtime", name: stack.join(" > "), modifier: chain[chain.length - 1], has_body: false, line: lineOf(node) });
      } else if (head === "assert" || head === "expect") {
        const args = head === "expect" ? (expectSubject(node) || { arguments: [] }).arguments.concat(node.arguments) : node.arguments;
        const argTexts = Array.from(args).map((a) => a.getText(sf));
        const literals = Array.from(args).filter(isLiteral).map((a) => a.getText(sf));
        let trivial = false;
        if (args.length >= 1 && args.every(isLiteral)) {
          trivial = argTexts.length === 1 ? ["true", "1", "!0"].includes(argTexts[0]) : argTexts.every((t) => t === argTexts[0]);
        } else if (argTexts.length >= 2 && argTexts[0] === argTexts[1]) {
          trivial = true;
        }
        const isOuter = !(ts.isPropertyAccessExpression(node.parent) || ts.isCallExpression(node.parent) && node.parent.expression === node);
        if (head === "assert" || isOuter) {
          assertions.push({
            callee: chain.join("."),
            args: argTexts,
            literals,
            test: stack.join(" > "),
            line: lineOf(node),
            in_try: tryDepth > 0,
            trivial,
          });
        }
      }
    }
    ts.forEachChild(node, visit);
    if (pushed) stack.pop();
  }
  visit(sf);
  const parseErrors = sf.parseDiagnostics ? sf.parseDiagnostics.length : 0;
  return { tests, assertions, parse_errors: parseErrors };
}

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => (input += c));
process.stdin.on("end", () => {
  const req = JSON.parse(input || "{}");
  const out = {};
  for (const [path, text] of Object.entries(req.files || {})) out[path] = analyse(path, text);
  process.stdout.write(JSON.stringify({ typescript: ts.version, files: out }));
});

package main

import (
    "encoding/json"
    "go/ast"
    "go/parser"
    "go/token"
    "os"
    "strings"
)

type FunctionInfo struct {
    Name       string   `json:"name"`
    Signature  string   `json:"signature"`
    Calls      []string `json:"calls"`
    SourceCode string   `json:"source_code"`
    Package    string   `json:"package"`
    IsTest     bool     `json:"is_test"`
    TestType   string   `json:"test_type"`
    TestParent string   `json:"test_parent"`
}

func extractCallExpr(expr ast.Expr) (string, bool) {
    switch x := expr.(type) {
    case *ast.Ident:
        return x.Name, true
    case *ast.SelectorExpr:
        if ident, ok := x.X.(*ast.Ident); ok {
            return ident.Name + "." + x.Sel.Name, true
        }
    }
    return "", false
}

func extractCalls(node ast.Node) []string {
    calls := []string{}
    ast.Inspect(node, func(n ast.Node) bool {
        if call, ok := n.(*ast.CallExpr); ok {
            if name, ok := extractCallExpr(call.Fun); ok {
                calls = append(calls, name)
            }
        }
        return true
    })
    return calls
}

func main() {
    filename := os.Args[1]
    fset := token.NewFileSet()
    node, err := parser.ParseFile(fset, filename, nil, parser.ParseComments)
    if err != nil {
        panic(err)
    }

    functions := []FunctionInfo{}
    var currentDescribe string

    ast.Inspect(node, func(n ast.Node) bool {
        switch x := n.(type) {
        case *ast.FuncDecl:
            params := []string{}
            if x.Type.Params != nil {
                for _, p := range x.Type.Params.List {
                    typeStr := ""
                    if expr, ok := p.Type.(*ast.Ident); ok {
                        typeStr = ":" + expr.Name
                    }
                    for _, name := range p.Names {
                        params = append(params, name.Name + typeStr)
                    }
                }
            }

            isTest := strings.HasPrefix(x.Name.Name, "Test")
            testType := ""
            if isTest {
                testType = "test"
            }
            
            functions = append(functions, FunctionInfo{
                Name:       x.Name.Name,
                Signature:  x.Name.Name + "(" + strings.Join(params, ", ") + ")",
                Calls:      extractCalls(x),
                SourceCode: fset.Position(x.Pos()).String(),
                Package:    node.Name.Name,
                IsTest:     isTest,
                TestType:   testType,
            })

        case *ast.CallExpr:
            funcName, ok := extractCallExpr(x.Fun)
            if !ok {
                return true
            }

            switch funcName {
            case "Describe", "G.Describe", "Context", "G.Context":
                if len(x.Args) > 0 {
                    if lit, ok := x.Args[0].(*ast.BasicLit); ok {
                        currentDescribe = strings.Trim(lit.Value, `"`)
                        functions = append(functions, FunctionInfo{
                            Name:       currentDescribe,
                            Signature:  funcName + "(" + currentDescribe + ")",
                            Calls:      extractCalls(x),
                            SourceCode: fset.Position(x.Pos()).String(),
                            Package:    node.Name.Name,
                            IsTest:     true,
                            TestType:   "describe",
                        })
                    }
                }
            case "It", "G.It", "G.DescribeTable":
                if len(x.Args) > 0 {
                    if lit, ok := x.Args[0].(*ast.BasicLit); ok {
                        testName := strings.Trim(lit.Value, `"`)
                        functions = append(functions, FunctionInfo{
                            Name:       testName,
                            Signature:  funcName + "(" + testName + ")",
                            Calls:      extractCalls(x),
                            SourceCode: fset.Position(x.Pos()).String(),
                            Package:    node.Name.Name,
                            IsTest:     true,
                            TestType:   "it",
                            TestParent: currentDescribe,
                        })
                    }
                }
            }
        }
        return true
    })

    json.NewEncoder(os.Stdout).Encode(functions)
}
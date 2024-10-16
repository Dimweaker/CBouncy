#pragma once
#include <map>
#include <memory>
#include <vector>

#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/AST/Type.h"

class VarAnalysisVisitor;

namespace clang {
class Decl;
class DeclGroupRef;
class ASTContext;
class CompilerInstance;
} // namespace clang

using namespace clang;

class VarScope;
class VarAnalysisVisitor;

class AddVarASTConsumer : public ASTConsumer {
    friend class VarAnalysisVisitor;

  public:
    AddVarASTConsumer(std::shared_ptr<CompilerInstance> &CI_sptr);
    ~AddVarASTConsumer();

    bool HandleTopLevelDecl(DeclGroupRef) override;
    void HandleTranslationUnit(ASTContext &ctx) override;

  private:
    std::shared_ptr<CompilerInstance> CI;
    VarAnalysisVisitor *visitor;
    VarScope *VS_root;
};
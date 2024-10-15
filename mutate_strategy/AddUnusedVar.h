#pragma once
#include <map>
#include <memory>
#include <vector>

#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"

class VarAnalysisVisitor;

namespace clang {
class Decl;
class DeclGroupRef;
class ASTContext;
class CompilerInstance;
class Scope;
} // namespace clang

using namespace clang;
class VarAnalysisVisitor;

class AddVarASTConsumer : public ASTConsumer {
    friend class VarAnalysisVisitor;

  public:
    AddVarASTConsumer(std::shared_ptr<CompilerInstance> &CI_sptr);
    ~AddVarASTConsumer();

    // bool HandleTopLevelDecl(DeclGroupRef) override;
    void HandleTranslationUnit(ASTContext &ctx) override;

  private:
    std::map<Scope *, std::vector<VarDecl *>> VD_map;
    std::shared_ptr<CompilerInstance> CI;
    VarAnalysisVisitor *visitor;
};
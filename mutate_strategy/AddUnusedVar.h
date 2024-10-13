#pragma once
#include <map>
#include <vector>
#include <memory>

#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"

class AddVarAnalysisVisitor;

namespace clang {
class Decl;
class DeclGroupRef;
class ASTContext;
class CompilerInstance;
}

using namespace clang;

class AddVarASTConsumer : public ASTConsumer {
    friend class AddVarAnalysisVisitor;
  public:
    AddVarASTConsumer();

    void setCompilerInstance(std::shared_ptr<CompilerInstance> CI_sptr) { CI = CI_sptr; };

    bool HandleTopLevelDecl(DeclGroupRef DR) override;

    void HandleTranslationUnit(ASTContext &ctx) override;

  private:
    std::map<Decl*, std::vector<VarDecl*>> VD_map; // nullptr means top level decl
    std::shared_ptr<CompilerInstance> CI;
};
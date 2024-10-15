#include "AddUnusedVar.h"
#include "iostream"

#include "clang/Basic/Builtins.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Sema/Scope.h"
#include "clang/Sema/Sema.h"
#include "clang/Sema/ScopeInfo.h"

#include "RewriteUtils.h"

class VarAnalysisVisitor : public RecursiveASTVisitor<VarAnalysisVisitor> {
    friend class AddVarASTConsumer;

  public:
    VarAnalysisVisitor(AddVarASTConsumer *consumer)
        : consumer(consumer), sema(nullptr) {}

    bool VisitVarDecl(VarDecl *);
    bool VisitFunctionDecl(FunctionDecl *FD);

  private:
    AddVarASTConsumer *consumer;
    Sema *sema;
};

bool VarAnalysisVisitor::VisitVarDecl(VarDecl *VD) {
    if (!sema)
        return true;

    std::cout << "find a var " << VD->getNameAsString() << std::endl;
    Scope *cur_scope = sema->getCurScope();
    if (cur_scope) {
        std::cout << "in scope " << cur_scope << std::endl;
    }
    return true;
}

bool VarAnalysisVisitor::VisitFunctionDecl(FunctionDecl *FD) {
    if (!sema)
        return true;

    std::cout << "find a func " << FD->getNameAsString() << std::endl;
    Scope *cur_scope = sema->getCurScope();
    if (cur_scope) {
        std::cout << "in scope " << cur_scope << std::endl;
    }
    return true;
}

AddVarASTConsumer::AddVarASTConsumer(std::shared_ptr<CompilerInstance> &CI_sptr)
    : visitor(new VarAnalysisVisitor(this)), CI(CI_sptr) {
    Initialize(CI->getASTContext());
}

AddVarASTConsumer::~AddVarASTConsumer() { delete visitor; }

// bool AddVarASTConsumer::HandleTopLevelDecl(DeclGroupRef DGR) { 
//     for(DeclGroupRef::iterator iter = DGR.begin(); iter != DGR.end(); iter++) {
//         visitor->TraverseDecl(*iter);
//     }
//     return true;
// }

void AddVarASTConsumer::HandleTranslationUnit(ASTContext &ctx) {
    visitor->sema = &CI->getSema();
    visitor->TraverseDecl(ctx.getTranslationUnitDecl());
}
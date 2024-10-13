#include "AddUnusedVar.h"
#include "iostream"

#include "clang/Basic/Builtins.h"
#include "clang/Frontend/CompilerInstance.h"

#include "RewriteUtils.h"

class AddVarAnalysisVisitor
    : public RecursiveASTVisitor<AddVarAnalysisVisitor> {
  public:
    AddVarAnalysisVisitor(AddVarASTConsumer *consumer) : consumer(consumer) {}

    bool VisitVarDecl(VarDecl *VD) {
        Decl *father_decl = cast<Decl>(VD->getDeclContext());
        if (father_decl) {
            std::cout << "find a local VD " << VD->getNameAsString() << " in "
                      << father_decl->getDeclKindName() << std::endl;
            consumer->VD_map[father_decl].emplace_back(VD);
        }
        return true;
    }

  private:
    AddVarASTConsumer *consumer;
};

AddVarASTConsumer::AddVarASTConsumer()
    // : analysis_visitor(std::make_unique<AddVarAnalysisVisitor>(this))
{}

bool AddVarASTConsumer::HandleTopLevelDecl(DeclGroupRef DR) {
    for (DeclGroupRef::iterator decl_iter = DR.begin(); decl_iter != DR.end(); decl_iter++) {
        VarDecl *VD = dyn_cast<VarDecl>(*decl_iter);
        if (VD) {
            // save global vars
            std::cout << "find a global VD " << VD->getNameAsString()
                      << std::endl;
            VD_map[nullptr].emplace_back(VD);
            continue;
        } 
        // else
            // analysis_visitor->TraverseDecl(*decl_iter);
    }
    return true;
}

void AddVarASTConsumer::HandleTranslationUnit(ASTContext &ctx) {
    
}
#include "AddUnusedVar.h"
#include <iostream>
#include <regex>
#include <stack>

#include "clang/Basic/Builtins.h"
#include "clang/Frontend/CompilerInstance.h"

#include "RewriteUtils.h"

std::string Cqualifiers[] = {"const", "volatile", "__restrict"};

/**
 * When calling @param HnadleTopLevelDecl() or @param HandleTranslationUnit()
 * here, Parser has already finished parsing, thus calling @param getCurScope()
 * in @param VarAnalysisVisitor makes no sense, it'll always return a scope
 * of type Top Decl.
 */

class VarScope {
  public:
    VarScope(VarScope *p = nullptr) : parent(p) {
        if (p)
            p->children.emplace_back(this);
    }

    void addVD(VarDecl *VD) { VDs.emplace_back(VD); }
    void addVD(std::vector<VarDecl *> buf) {
        for (auto &VD : buf)
            VDs.emplace_back(VD);
    }

    void print(int depth=0) {
        for(int i=0; i<depth; i++)
            std::cout << "\t";
        std::cout << "scope: \n";
        for(auto VD: VDs) {
            for(int i=0; i<=depth; i++)
                std::cout << "\t";
            std::cout << "VD " << VD->getNameAsString() << "\n";
        }
        for(auto scope : children)
            scope->print(depth+1);
    }

  private:
    std::vector<VarDecl *> VDs;
    VarScope *parent;
    std::vector<VarScope *> children;
};

class VarAnalysisVisitor : public RecursiveASTVisitor<VarAnalysisVisitor> {
    friend class AddVarASTConsumer;

  public:
    VarAnalysisVisitor(AddVarASTConsumer *consumer)
        : consumer(consumer), src_mgr(&consumer->CI->getSourceManager()) {}

    bool VisitVarDecl(VarDecl *);
    bool TraverseIfStmt(IfStmt *);
    bool TraverseSwitchStmt(SwitchStmt *SS);

#ifndef TRAVERSE_BODY
#define TRAVERSE_BODY(CLASS)                                                   \
    bool Traverse##CLASS(CLASS *ptr) {                                         \
        if (Stmt *Body = ptr->getBody()) {                                     \
            push_VS();                                                         \
            TraverseStmt(Body);                                                \
            pop_VS();                                                          \
        }                                                                      \
        return true;                                                           \
    }
#endif
    TRAVERSE_BODY(FunctionDecl)
    TRAVERSE_BODY(ForStmt)
    TRAVERSE_BODY(WhileStmt)
    TRAVERSE_BODY(DoStmt)
#undef TRAVERSE_BODY

  private:
    AddVarASTConsumer *consumer;
    SourceManager *src_mgr;
    std::stack<VarScope *> VS_stack;

    void push_VS() {
        if (VS_stack.empty())
            VS_stack.push(new VarScope());
        else
            VS_stack.push(new VarScope(VS_stack.top()));
    }

    VarScope *pop_VS() {
        assert(!VS_stack.empty() && "pop before pushing!");
        VarScope *top = VS_stack.top();
        VS_stack.pop();
        return top;
    };
};

void replaceAll(std::string &s, const std::string &pattern,
                const std::string &dst) {
    std::size_t pos = s.find(pattern);
    while (pos != std::string::npos) {
        s.replace(pos, pattern.size(), dst);
        pos = s.find(pattern);
    }
}

void normalize(std::string &s) {
    /**
     * remove all whitespace before and after @param s
     * convert all [*] into stars.
     * shrink all continuous whitespace into one
     * remove all whitespace between stars
     */
    s.erase(0, s.find_first_not_of(' '));
    s.erase(s.find_last_not_of(' ') + 1);

    std::regex pattern("\\[.*?\\]");
    s = std::regex_replace(s, pattern, " *");

    replaceAll(s, "  ", " ");
    replaceAll(s, "* ", "*");
}

bool VarAnalysisVisitor::VisitVarDecl(VarDecl *VD) {
    if (!VD->isCanonicalDecl() || VD->isInvalidDecl())
        return true;
    // ignore param VD
    if (isa<ParmVarDecl>(VD))
        return true;
    // ignore VD outside the file
    SourceLocation loc = VD->getLocation();
    if (!src_mgr->isInMainFile(loc))
        return true;

    // add VD to buffer
    std::string type = VD->getType().getAsString();
    for (auto &qualifier : Cqualifiers) {
        replaceAll(type, qualifier, "");
    }
    normalize(type);

    VS_stack.top()->addVD(VD);

    return true;
}

bool VarAnalysisVisitor::TraverseIfStmt(IfStmt *IS) {
    if (Expr *Cond = IS->getCond()) {
        if (!TraverseStmt(Cond))
            return false;
    }

#ifndef TRAVERSE_STMT
#define TRAVERSE_STMT(BRANCH)                                                  \
    if (Stmt *BRANCH = IS->get##BRANCH()) {                                    \
        push_VS();                                                             \
        TraverseStmt(BRANCH);                                                  \
        pop_VS();                                                              \
    }

#endif
    TRAVERSE_STMT(Then)
    TRAVERSE_STMT(Else)
#undef TRAVERSE_STMT

    return true;
}

bool VarAnalysisVisitor::TraverseSwitchStmt(SwitchStmt *SS) {
    for (SwitchCase *Case = SS->getSwitchCaseList(); Case;
         Case = Case->getNextSwitchCase()) {
        push_VS();
        TraverseStmt(Case);
        pop_VS();
    }
    return true;
}

AddVarASTConsumer::AddVarASTConsumer(std::shared_ptr<CompilerInstance> &CI_sptr)
    : visitor(new VarAnalysisVisitor(this)), CI(CI_sptr), VS_root(nullptr) {}

AddVarASTConsumer::~AddVarASTConsumer() { delete visitor; }

bool AddVarASTConsumer::HandleTopLevelDecl(DeclGroupRef DGR) { return true; }

void AddVarASTConsumer::HandleTranslationUnit(ASTContext &ctx) {
    visitor->push_VS();
    visitor->TraverseTranslationUnitDecl(ctx.getTranslationUnitDecl());
    VS_root = visitor->pop_VS();

    VS_root->print();
}
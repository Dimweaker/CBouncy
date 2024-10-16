#include "AddUnusedVar.h"
#include <iostream>
#include <regex>
#include <stack>

#include "clang/Basic/Builtins.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Sema/ScopeInfo.h"

#include "RewriteUtils.h"

std::string Cqualifiers[] = {"const", "volatile", "__restrict"};

/**
 * When calling @param HnadleTopLevelDecl() or @param HandleTranslationUnit()
 * here, Parser has already finished parsing, thus calling @param getCurScope()
 * in @param VarAnalysisVisitor makes no sense, it'll always return a scope
 * of type Top Decl.
 *
 * the visitor visits and stores VD in order
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
    bool VisitFunctionDecl(FunctionDecl *);
    
    bool VisitForStmt(ForStmt *FS);
    bool VisitIfStmt(IfStmt *IS);

  private:
    AddVarASTConsumer *consumer;
    SourceManager *src_mgr;
    std::vector<VarDecl *> VDBuffer;
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
    std::cout << "visit VD " << VD->getNameAsString()<< std::endl;

    VDBuffer.emplace_back(VD);
    return true;
}

bool VarAnalysisVisitor::VisitFunctionDecl(FunctionDecl *FD) {
    std::cout << "visit FD" << std::endl;
    return true;
}

bool VarAnalysisVisitor::VisitForStmt(ForStmt *FS) {
    std::cout << "visit FS" << std::endl;
    return true;
}

bool VarAnalysisVisitor::VisitIfStmt(IfStmt *IS) {
    std::cout << "visit IS" << std::endl;
    return true;
}

AddVarASTConsumer::AddVarASTConsumer(std::shared_ptr<CompilerInstance> &CI_sptr)
    : visitor(new VarAnalysisVisitor(this)), CI(CI_sptr) {}

AddVarASTConsumer::~AddVarASTConsumer() { delete visitor; }

bool AddVarASTConsumer::HandleTopLevelDecl(DeclGroupRef DGR) { 
    return true;
}

void AddVarASTConsumer::HandleTranslationUnit(ASTContext &ctx) {
    visitor->TraverseTranslationUnitDecl(ctx.getTranslationUnitDecl());
}
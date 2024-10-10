#include "iostream"

#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Basic/Builtins.h"
#include "clang/Basic/Diagnostic.h"
#include "clang/Basic/FileManager.h"
#include "clang/Basic/TargetInfo.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Lex/PreprocessorOptions.h"
#include "clang/Parse/ParseAST.h"
#include "clang/Rewrite/Core/Rewriter.h"

#include "RewriteUtils.h"

using namespace clang;
using namespace llvm;

class AddVarASTConsumer;
AddVarASTConsumer *consumer;

class AddVarASTVisitor : public RecursiveASTVisitor<AddVarASTVisitor> {
  public:
    AddVarASTVisitor() {}

    bool VisitVarDecl(VarDecl *VD) {
        // if global
        if (VD->hasGlobalStorage()) {
            std::string vartype = VD->getType().getAsString(),
                        varname = VD->getNameAsString();
            std::string insertstr = 
                vartype + " *"+ varname +"_proxy = &"+varname + ";"; 
            RewriteUtils::getInstance()->addStringAfterVarDecl(VD, insertstr);
        }
        return true;
    }
};

class AddVarASTConsumer : public ASTConsumer {
  public:
    AddVarASTConsumer() {}

    bool HandleTopLevelDecl(DeclGroupRef DR) override {
        for (auto Decl : DR) {
            visitor.TraverseDecl(Decl);  // 遍历所有声明
        }
        return true;
    }

  private:
    AddVarASTVisitor visitor;
};

std::unique_ptr<CompilerInstance> getCompilerInstance(std::string infile) {
    std::unique_ptr<CompilerInstance> CI = std::make_unique<CompilerInstance>();
    assert(CI && "failed to initialize CI!");

    CI->createDiagnostics();

    PreprocessorOptions &PPOpts = CI->getPreprocessorOpts();
    CI->getTargetOpts().Triple = LLVM_DEFAULT_TARGET_TRIPLE;
    llvm::Triple T(LLVM_DEFAULT_TARGET_TRIPLE);
    CI->getLangOpts().setLangDefaults(CI->getLangOpts(), Language::C, T,
                                      PPOpts.Includes);

    TargetInfo *Target = TargetInfo::CreateTargetInfo(
        CI->getDiagnostics(), CI->getInvocation().TargetOpts);
    CI->setTarget(Target);

    CI->createFileManager();
    CI->createSourceManager(CI->getFileManager());
    CI->createPreprocessor(TU_Complete);

    DiagnosticConsumer &DgClient = CI->getDiagnosticClient();
    DgClient.BeginSourceFile(CI->getLangOpts(), &CI->getPreprocessor());
    CI->createASTContext();

    InputKind IK = FrontendOptions::getInputKindForExtension(
        StringRef(infile).rsplit('.').second);
    assert(CI->InitializeSourceManager(FrontendInputFile(infile, IK)) &&
           "initialize infile failed!");

    return CI;
}

int main(int argc, char **argv) {
    assert(argc == 3 && "should take two args!");
    std::string infile = argv[1], outfile = argv[2];

    // init compiler instance
    std::unique_ptr<CompilerInstance> CI = getCompilerInstance(infile);
    clang::ASTContext &ctx = CI->getASTContext();
    clang::SourceManager &src_mgr = ctx.getSourceManager();
    
    // get RU
    RewriteUtils::createInstance();
    RU_sptr RUinstance = RewriteUtils::getInstance();
    RUinstance->initialize(src_mgr, CI->getLangOpts());
    
    // set consumer
    consumer = new AddVarASTConsumer();
    CI->setASTConsumer(std::unique_ptr<AddVarASTConsumer>(consumer));

    // create sema
    CI->createSema(TU_Complete, 0);
    DiagnosticsEngine &Diag = CI->getDiagnostics();
    Diag.setSuppressAllDiagnostics(true);
    Diag.setIgnoreAllWarnings(true);

    // traverse AST
    clang::ParseAST(CI->getSema());

    RUinstance->outputTransformedFile(outfile);
}

#include "clang/Basic/Diagnostic.h"
#include "clang/Basic/FileManager.h"
#include "clang/Basic/TargetInfo.h"
#include "clang/Lex/PreprocessorOptions.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Parse/ParseAST.h"

#include "RewriteUtils.h"
#include "AddUnusedVar.h"

std::shared_ptr<CompilerInstance> getCompilerInstance(std::string infile) {
    std::shared_ptr<CompilerInstance> CI = std::make_shared<CompilerInstance>();
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

    return std::move(CI);
}

int main(int argc, char **argv) {
    assert(argc == 3 && "should take two args!");
    std::string infile = argv[1], outfile = argv[2];

    // init compiler instance
    std::shared_ptr<CompilerInstance> CI = getCompilerInstance(infile);
    clang::ASTContext &ctx = CI->getASTContext();
    clang::SourceManager &src_mgr = ctx.getSourceManager();

    // get RewriteUtils
    RewriteUtils::createInstance();
    RU_sptr RUinstance = RewriteUtils::getInstance();
    RUinstance->initialize(src_mgr, CI->getLangOpts());

    // set consumer
    std::unique_ptr<AddVarASTConsumer> consumer =
        std::make_unique<AddVarASTConsumer>(CI);
    CI->setASTConsumer(std::move(consumer));

    // create sema
    CI->createSema(TU_Complete, 0);
    DiagnosticsEngine &Diag = CI->getDiagnostics();
    Diag.setSuppressAllDiagnostics(false);
    Diag.setIgnoreAllWarnings(false);

    // traverse AST
    clang::ParseAST(CI->getSema());

    RUinstance->outputTransformedFile(outfile);
}
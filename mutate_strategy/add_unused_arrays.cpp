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
#include "llvm/Support/raw_ostream.h"

using namespace clang;
using namespace llvm;

class AddVarASTConsumer;
AddVarASTConsumer *consumer;

class AddVarASTVisitor : public RecursiveASTVisitor<AddVarASTVisitor> {
  public:
    AddVarASTVisitor(Rewriter &Prewriter):rewriter(&Prewriter)  {}

    bool VisitVarDecl(VarDecl *vd) {
        // if global
        if (vd->hasGlobalStorage()) {
            std::string vartype = vd->getType().getAsString();
            std::string varname = vd->getNameAsString();

            // get Loc after semi
            SourceLocation VDEndLoc = vd->getEndLoc();
            SourceManager &mgr = rewriter->getSourceMgr();
            const char *buf = mgr.getCharacterData(VDEndLoc);
            int offset = 0;
            while (*buf != ';') {
                buf++;
                if(*buf == '\0') break;
                offset++;
            }
            offset++;
            VDEndLoc = VDEndLoc.getLocWithOffset(offset);
            rewriter->InsertText(VDEndLoc, "\n" + vartype + "* " + "b=&" + varname+";");
        }
        return true;
    }

  private:
    Rewriter *rewriter;
};

class AddVarASTConsumer : public ASTConsumer {
  public:
    AddVarASTConsumer(Rewriter &rewriter): visitor(rewriter), mgr(nullptr) {}

    void setMgr(SourceManager *Pmgr) {
        assert(!mgr && "mgr already set!");
        mgr = Pmgr;
    }

    bool HandleTopLevelDecl(DeclGroupRef DR) override {
        for (auto Decl : DR) {
            visitor.TraverseDecl(Decl);  // 遍历所有声明
        }
        return true;
    }

  private:
    SourceManager *mgr;
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

llvm::raw_ostream *getOutStream(std::string outfile) {
    if (outfile.empty())
        return &(llvm::outs());

    std::error_code EC;
    llvm::raw_fd_ostream *Out = new llvm::raw_fd_ostream(
        outfile, EC, llvm::sys::fs::FA_Read | llvm::sys::fs::FA_Write);
    assert(!EC && "Cannot open output file!");
    return Out;
}

int main(int argc, char **argv) {
    assert(argc == 3 && "should take two args!");
    std::string infile = argv[1], outfile = argv[2];

    // init compiler instance
    std::unique_ptr<CompilerInstance> CI = getCompilerInstance(infile);
    // get rewriter
    clang::ASTContext &ctx = CI->getASTContext();
    clang::SourceManager &src_mger = ctx.getSourceManager();
    clang::Rewriter rewriter;
    rewriter.setSourceMgr(src_mger, ctx.getLangOpts());
    // set consumer
    assert(!consumer && "consumer already initialized");
    consumer = new AddVarASTConsumer(rewriter);
    consumer->setMgr(&CI->getSourceManager());
    CI->setASTConsumer(std::unique_ptr<AddVarASTConsumer>(consumer));
    // create sema
    CI->createSema(TU_Complete, 0);
    DiagnosticsEngine &Diag = CI->getDiagnostics();
    Diag.setSuppressAllDiagnostics(true);
    Diag.setIgnoreAllWarnings(true);

    clang::ParseAST(CI->getSema());

    // write transformed file
    FileID MainFileID = src_mger.getMainFileID();
    const RewriteBuffer *RWBuf = rewriter.getRewriteBufferFor(MainFileID);
    llvm::raw_ostream *os = getOutStream(outfile);
    if (RWBuf) {
        std::cout << "file changed" << std::endl;
        *os << std::string(RWBuf->begin(), RWBuf->end());
    } else {
        std::cout << "file unchanged" << std::endl;
        FileID MainFileID = src_mger.getMainFileID();
        auto MainBuf = src_mger.getBufferOrNone(MainFileID);
        *os << MainBuf->getBufferStart();
    }
    // flush and close stream
    os->flush();
    delete os;
}

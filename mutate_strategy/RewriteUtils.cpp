#include "RewriteUtils.h"

#include <iostream>

#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "llvm/Support/raw_ostream.h"

RU_Sptr RewriteUtils::RUinstance = nullptr;

void RewriteUtils::createInstance() {
    assert(!RUinstance && "RU instance already created!");
    RUinstance = RU_Sptr(new RewriteUtils());
}

RU_Sptr RewriteUtils::getInstance() {
    assert(RUinstance && "RU instance not created!");
    return RUinstance;
}

RewriteUtils::RewriteUtils() : rewriter(nullptr), src_mgr(nullptr) {}

void RewriteUtils::initialize(SourceManager & Psrc_mgr, LangOptions &LO) {
    assert(!rewriter && "RewriteUtils already initialized!");
    rewriter = std::make_unique<Rewriter>();
    rewriter->setSourceMgr(Psrc_mgr, LO);
    src_mgr = &Psrc_mgr;
}

RewriteUtils::~RewriteUtils() {
}

bool RewriteUtils::addStringAfterVarDecl(VarDecl *VD, std::string &str) {
    SourceLocation VDEndLoc = VD->getEndLoc();
    if (VDEndLoc.isInvalid())
        return false;

    SourceLocation insertLoc = getLocAfterSymbol(VDEndLoc, ';');
    return !rewriter->InsertText(insertLoc, str);
}

SourceLocation RewriteUtils::getLocAfterSymbol(SourceLocation Loc,
                                               char symbol) {
    const char *buf = src_mgr->getCharacterData(Loc);
    int offset = getOffsetUntilSymbol(buf, symbol);
    offset++;
    return Loc.getLocWithOffset(offset);
}

int RewriteUtils::getOffsetUntilSymbol(const char *buf, char symbol) {
    int offset = 0;
    while (*buf != symbol) {
        buf++;
        if (*buf == '\0')
            break;
        offset++;
    }
    return offset;
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

bool RewriteUtils::outputTransformedFile(std::string &outfile) {
    // write transformed file
    FileID MainFileID = src_mgr->getMainFileID();
    const RewriteBuffer *RWBuf = rewriter->getRewriteBufferFor(MainFileID);
    llvm::raw_ostream *os = getOutStream(outfile);
    if (RWBuf) {
        std::cout << "file changed" << std::endl;
        *os << std::string(RWBuf->begin(), RWBuf->end());
    } else {
        std::cout << "file unchanged" << std::endl;
        FileID MainFileID = src_mgr->getMainFileID();
        auto MainBuf = src_mgr->getBufferOrNone(MainFileID);
        *os << MainBuf->getBufferStart();
    }
    // flush and close stream
    os->flush();
    delete os;
    return true;
}
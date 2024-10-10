#pragma once

#include <memory>

#include "clang/Basic/SourceManager.h"
#include "clang/Rewrite/Core/Rewriter.h"

namespace clang {
class VarDecl;
class LangOptions;
} // namespace clang

namespace llvm {
class raw_ostream;
}

class RewriteUtils;
using RU_sptr = std::shared_ptr<RewriteUtils>;
using namespace clang;
using namespace llvm;

class RewriteUtils {
  public:
    static void createInstance();
    static RU_sptr getInstance();

    ~RewriteUtils();

    void initialize(SourceManager &, LangOptions &);

    bool addStringAfterVarDecl(VarDecl *, std::string &);

    bool outputTransformedFile(std::string &);

  private:
    RewriteUtils();

    int getOffsetUntilSymbol(const char *, char);

    SourceLocation getLocAfterSymbol(SourceLocation, char);

  private:
    static RU_sptr RUinstance;

    std::unique_ptr<Rewriter> rewriter;
    SourceManager *src_mgr;
};

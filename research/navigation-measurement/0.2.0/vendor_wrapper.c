/* Original bounded wrapper around the separately authored, pinned OxTS decoder.
 * Vendor source is supplied privately and remains unchanged. No networking. */
#include <stdio.h>
#include "NComRxC.h"

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *input = fopen(argv[1], "rb");
    if (!input) return 3;
    NComRxC *decoder = NComCreateNComRxC();
    if (!decoder) { fclose(input); return 4; }
    int value;
    long count = 0;
    while ((value = fgetc(input)) != EOF) {
        if (++count > 72000) { NComDestroyNComRxC(decoder); fclose(input); return 5; }
        if (NComNewChar(decoder, (unsigned char)value) == COM_NEW_UPDATE) {
            printf("%ld,%u,%u,%d,%.17g,%d,%.17g\n", count - 1,
                decoder->mInsNavMode, decoder->mOutputPacketType,
                decoder->mIsTimeValid, decoder->mTime,
                decoder->mIsVnValid, decoder->mVn);
        }
    }
    int failed = ferror(input) || ferror(stdout);
    NComDestroyNComRxC(decoder);
    fclose(input);
    return failed ? 6 : 0;
}

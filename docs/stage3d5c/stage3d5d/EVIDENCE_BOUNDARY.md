# Evidence defect isolation and new contract

Old Stage5C artifact14181928387 is retained unchanged. Independent inspection finds30manifest-listed hidden source paths absent in ZIP. Its fixed workflow cad-prototype.yml first creates source via git archive HEAD, then upload-artifact@v4 without include-hidden-files. Recorded job132969915392 resolves action ea165f8d65b6e75b540449e92b4886f43607fa02 and logs include-hidden-files:false/1386selected files. Reconstructed git archive at fixedHEAD has1413paths whose bytes match the old manifest; uploaded source1383 differs by exactly30dot-path members.

Inference: evidence strongly localizes omission to upload selection. The historical pre-upload filesystem raw snapshot was not retained, so reconstruction is not contemporaneous observation of that directory. GitHub-original ZIP and Library readback are byte-equal, ruling out loss during that storage/readback transfer. Missing members are not restored by a later supplement. Old completeness staysPARTIAL.

Source-free18ZIP are a separate collection-scope limitation; absence alone is not proof of upload loss. Their results/image meanings were not independently audited in5C. This5D does not declare them retroactively audited.

New audit_archive requires an independently fixed expected member inventory including hidden names, rejects missing/extra/duplicate/path violations, checks bytes and CRC, and makes no semanticCAD claim. Synthetic complete/hidden-omitted/source-freeZIPs and full expected inventories are retained. They reproduce the coverage distinction without rewriting old artifacts.

All existing1413assets/workflows remain unchanged. The requested distinct new dedicated5Dworkflow isBLOCKED because its new path would violate immutable5C collector policy. New5Dtests run inside inherited5Cunit discovery with separatecase names/artifact subdirectories, not a newdedicatedCI substitute. Existing5C upload includes hiddenfiles; the added hidden source sentinel is checked in the new original artifact. ActualOCP absence is recordedBLOCKED independently of passing environment-handling tests. Mock and realenvironment probes are labelled separately.

New formal artifacts, old artifact and later packaging/inspection notes have distinct identities. Hash/CRC agreement establishes saved-byte integrity, not missing-evidence completeness, native-set validity or future retention. No public privateLibrary links or IDs.

# KRpep-Zero project overview

This is a computational chemistry/control-validation study with a negative selection result. The original novel-binder objective remains unmet. No new affinity, mutant selectivity or biological activity is established.

## Navigation

1. **Overview:** 18 saved control predictions means 12 Boltz predictions plus 6 Protenix base diagnostics, across two peptide identities. The two generator pilot designs were rejected; the main candidate campaign was not run.
2. **Compare structures:** begin with the experimental 5XCO reference. Choose a model/representation, control and seed. Teal is the selected prediction; magenta is experimental KRpep-2d. Only one prediction is overlaid at a time.
3. **All 18 runs:** inspect every seed in fixed order. For example, Boltz revision 1 seed 42 has the highest positive confidence in that revision but a displaced pose. Inspect seeds 17 and 101 too; none is omitted or selected as a winning design.
4. **Boltz results and Protenix:** revision 2 passes the measured chemistry checks but fails the original confidence separation. Protenix base recovers 0/41 native contacts in all three positive-control seeds and fails the reported chemistry checks. Neither result supports candidate advancement.
5. **Study package:** open the report, one-page brief or editable presentation. Further candidate selection requires experimentally characterized controls and held-out evaluation.

## Comparison controls

- **Fit all:** include the selected prediction and reference in view.
- **Reference pocket / Prediction focus:** focus on one peptide location. These camera controls do not move molecular coordinates.
- **Target surface / Reference peptide / Predicted target:** toggle scene layers. The predicted target is hidden by default to keep the pose comparison legible.
- **Rotate:** start/stop view rotation.
- **View pose:** jump from any of the 18 table rows to that recorded result.
- **Figures:** click or keyboard-activate a plot to enlarge it; press Escape or Close to return.
- **Original CIF:** download the untouched prediction in its original coordinate frame. The browser overlay uses a separate, target-aligned display asset.

All overlays fit 169 matched target Cα atoms using a proper rigid transform. The same transform is applied to the entire prediction; the peptide is never independently fitted. Positive peptide core RMSD uses Cα atoms 5–15 (11 atoms) and matches the saved audit. No native-pose RMSD/contact metric is assigned to the scrambled sequence. Displayed peptide connectivity follows the declared input graph; display is not proof that chemistry checks pass.

## Start the local demo

From the downloaded repository/export folder, run:

```sh
python3 -m http.server 8873 --bind 127.0.0.1 --directory dashboard
```

Open `http://127.0.0.1:8873/`. Serving the saved demo needs only Python's standard library; it does not run models or require API keys. The browser uses bundled viewer code and local assets. This localhost address works only on the computer running the server.

The public release includes the raw scientific files and all generated display assets. See README.md for the separate saved-data analysis reproduction command and its dependencies.

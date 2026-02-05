import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/robot_provider.dart';

class ControlsScreen extends StatefulWidget {
  const ControlsScreen({super.key});

  @override
  State<ControlsScreen> createState() => _ControlsScreenState();
}

class _ControlsScreenState extends State<ControlsScreen> {
  Timer? _cameraTimer;
  int _refreshKey = 0;

  @override
  void initState() {
    super.initState();
    // Refresh camera every 200ms
    _cameraTimer = Timer.periodic(const Duration(milliseconds: 200), (timer) {
      if (mounted) {
        setState(() {
          _refreshKey++;
        });
      }
    });
  }

  @override
  void dispose() {
    _cameraTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final robotProvider = Provider.of<RobotProvider>(context);
    final isConnected = robotProvider.isConnected;
    final snapshotUrl = robotProvider.getSnapshotUrl();

    return Scaffold(
      appBar: AppBar(title: const Text('Remote Control')),
      body: !isConnected
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.signal_wifi_off,
                    size: 64,
                    color: Colors.grey,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Robot not connected',
                    style: GoogleFonts.poppins(
                      fontSize: 18,
                      color: Colors.grey,
                    ),
                  ),
                ],
              ),
            )
          : Column(
              children: [
                Expanded(
                  flex: 2,
                  child: Center(
                    child: Container(
                      margin: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.black,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.grey.shade800),
                      ),
                      clipBehavior: Clip.antiAlias,
                      child: snapshotUrl != null
                          ? Image.network(
                              '$snapshotUrl?t=$_refreshKey',
                              fit: BoxFit.cover,
                              gaplessPlayback: true,
                              width: double.infinity,
                              height: double.infinity,
                              errorBuilder: (context, error, stackTrace) {
                                return Center(
                                  child: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      const Icon(
                                        Icons.videocam_off,
                                        color: Colors.white54,
                                      ),
                                      const SizedBox(height: 8),
                                      Text(
                                        'Camera Offline',
                                        style: GoogleFonts.poppins(
                                          color: Colors.white54,
                                        ),
                                      ),
                                    ],
                                  ),
                                );
                              },
                            )
                          : const Center(child: CircularProgressIndicator()),
                    ),
                  ),
                ),
                Expanded(
                  flex: 3,
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      children: [
                        _buildDirectionBtn(
                          Icons.arrow_upward,
                          'Forward',
                          () => robotProvider.sendMoveCommand(
                            1.0,
                            0.0,
                          ), // Linear 1, Angular 0
                        ),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                          children: [
                            _buildDirectionBtn(
                              Icons.arrow_back,
                              'Left',
                              () => robotProvider.sendMoveCommand(
                                0.0,
                                1.0,
                              ), // Linear 0, Angular 1
                            ),
                            _buildDirectionBtn(
                              Icons.stop,
                              'Stop',
                              () => robotProvider.sendMoveCommand(0.0, 0.0),
                              isStop: true,
                            ),
                            _buildDirectionBtn(
                              Icons.arrow_forward,
                              'Right',
                              () => robotProvider.sendMoveCommand(
                                0.0,
                                -1.0,
                              ), // Linear 0, Angular -1
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        _buildDirectionBtn(
                          Icons.arrow_downward,
                          'Backward',
                          () => robotProvider.sendMoveCommand(
                            -1.0,
                            0.0,
                          ), // Linear -1, Angular 0
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildDirectionBtn(
    IconData icon,
    String label,
    VoidCallback onPressed, {
    bool isStop = false,
  }) {
    return Column(
      children: [
        GestureDetector(
          onTapDown: (_) => onPressed(), // Send on press
          onTapUp: (_) {
            if (!isStop) {
              // Optional: Stop on release? For now, we just invoke the command once per click
              // or maybe we want a continuous press behavior?
              // The request asked for commands to be sent.
            }
          },
          child: ElevatedButton(
            onPressed: onPressed,
            style: ElevatedButton.styleFrom(
              backgroundColor: isStop
                  ? Colors.red.shade100
                  : Colors.blue.shade50,
              foregroundColor: isStop ? Colors.red : Colors.blue,
              shape: const CircleBorder(),
              padding: const EdgeInsets.all(24),
            ),
            child: Icon(icon, size: 32),
          ),
        ),
        const SizedBox(height: 8),
        Text(label, style: const TextStyle(fontSize: 12)),
      ],
    );
  }
}

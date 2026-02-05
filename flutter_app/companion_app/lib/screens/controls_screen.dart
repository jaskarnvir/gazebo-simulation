import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/robot_provider.dart';

class ControlsScreen extends StatelessWidget {
  const ControlsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final robotProvider = Provider.of<RobotProvider>(context);
    final isConnected = robotProvider.isConnected;

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
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.black12,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        'Camera Feed Placeholder',
                        style: GoogleFonts.poppins(color: Colors.black54),
                      ),
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
                          () {},
                        ),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                          children: [
                            _buildDirectionBtn(Icons.arrow_back, 'Left', () {}),
                            _buildDirectionBtn(
                              Icons.stop,
                              'Stop',
                              () {},
                              isStop: true,
                            ),
                            _buildDirectionBtn(
                              Icons.arrow_forward,
                              'Right',
                              () {},
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        _buildDirectionBtn(
                          Icons.arrow_downward,
                          'Backward',
                          () {},
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
        ElevatedButton(
          onPressed: onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: isStop ? Colors.red.shade100 : Colors.blue.shade50,
            foregroundColor: isStop ? Colors.red : Colors.blue,
            shape: const CircleBorder(),
            padding: const EdgeInsets.all(24),
          ),
          child: Icon(icon, size: 32),
        ),
        const SizedBox(height: 8),
        Text(label, style: const TextStyle(fontSize: 12)),
      ],
    );
  }
}

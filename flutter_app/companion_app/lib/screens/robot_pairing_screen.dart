import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import '../providers/robot_provider.dart';

class RobotPairingScreen extends StatefulWidget {
  const RobotPairingScreen({super.key});

  @override
  State<RobotPairingScreen> createState() => _RobotPairingScreenState();
}

class _RobotPairingScreenState extends State<RobotPairingScreen> {
  @override
  void initState() {
    super.initState();
    // Fetch robots when screen loads
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<RobotProvider>().loadRobots();
    });
  }

  void _showAddRobotDialog(BuildContext context) {
    final nameController = TextEditingController();
    final serialController = TextEditingController();
    bool isLoading = false;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) {
          return AlertDialog(
            title: Text(
              'Add New Robot',
              style: GoogleFonts.poppins(fontWeight: FontWeight.bold),
            ),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: nameController,
                  decoration: const InputDecoration(
                    labelText: 'Robot Name',
                    hintText: 'e.g., My MiRo',
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: serialController,
                  decoration: const InputDecoration(
                    labelText: 'Serial Number',
                    hintText: 'e.g., SN-12345',
                  ),
                ),
                if (isLoading) ...[
                  const SizedBox(height: 16),
                  const CircularProgressIndicator(),
                ],
              ],
            ),
            actions: [
              TextButton(
                onPressed: isLoading ? null : () => Navigator.pop(context),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: isLoading
                    ? null
                    : () async {
                        setState(() => isLoading = true);
                        try {
                          await context.read<RobotProvider>().addRobot(
                            nameController.text,
                            serialController.text,
                          );
                          if (context.mounted) {
                            Navigator.pop(context);
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Robot added successfully!'),
                              ),
                            );
                          }
                        } catch (e) {
                          if (context.mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Error: ${e.toString()}')),
                            );
                          }
                        } finally {
                          if (context.mounted) {
                            setState(() => isLoading = false);
                          }
                        }
                      },
                child: const Text('Add'),
              ),
            ],
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final robotProvider = context.watch<RobotProvider>();

    return Scaffold(
      appBar: AppBar(title: Text('Pair Robot', style: GoogleFonts.poppins())),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showAddRobotDialog(context),
        icon: const Icon(Icons.add),
        label: const Text('Add Robot'),
      ),
      body: robotProvider.isLoading && robotProvider.robots.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : robotProvider.robots.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.smart_toy_outlined,
                    size: 64,
                    color: Colors.grey,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'No robots found',
                    style: GoogleFonts.poppins(
                      fontSize: 18,
                      color: Colors.grey,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Add a robot to get started',
                    style: GoogleFonts.poppins(color: Colors.grey[600]),
                  ),
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: robotProvider.robots.length,
              itemBuilder: (context, index) {
                final robot = robotProvider.robots[index];
                final isConnected = robotProvider.selectedRobot?.id == robot.id;

                return Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: isConnected
                          ? Colors.green.shade100
                          : Colors.blue.shade100,
                      child: Icon(
                        Icons.smart_toy,
                        color: isConnected ? Colors.green : Colors.blue,
                      ),
                    ),
                    title: Text(
                      robot.name,
                      style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
                    ),
                    subtitle: Text('SN: ${robot.serialNumber}'),
                    trailing: ElevatedButton(
                      onPressed: isConnected
                          ? () {
                              robotProvider.disconnect();
                            }
                          : () {
                              robotProvider.selectRobot(robot);
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('Connected to ${robot.name}'),
                                ),
                              );
                              context
                                  .pop(); // Go back to dashboard after connecting
                            },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: isConnected
                            ? Colors.red.shade50
                            : null,
                        foregroundColor: isConnected ? Colors.red : null,
                      ),
                      child: Text(isConnected ? 'Disconnect' : 'Connect'),
                    ),
                  ),
                );
              },
            ),
    );
  }
}
